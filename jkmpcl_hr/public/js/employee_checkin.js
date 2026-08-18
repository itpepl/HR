const greenIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const redIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const blueIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

frappe.ui.form.on("Employee Checkin", {
    refresh(frm) {
        // Wait until the HTML field is rendered
        setTimeout(() => {
            render_map(frm);
        }, 100);
    }
});

function render_map(frm) {

    const field = frm.fields_dict.custom_route_map;

    if (!field) {
        console.error("HTML field 'custom_route_map' not found.");
        return;
    }

    // -----------------------------------------
    // Remove previous map
    // -----------------------------------------

    if (frm.employee_route_map) {
        try {
            frm.employee_route_map.remove();
        } catch (e) {
            console.warn("Error removing old map:", e);
        }

        frm.employee_route_map = null;
    }

    // -----------------------------------------
    // Create map container
    // -----------------------------------------

    field.$wrapper.html(`
        <div id="employee_route_map"
            style="
                height:500px;
                width:100%;
                border-radius:8px;
                margin-top:20px;
                margin-bottom:10px;
                border:1px solid #ccc;
                position:relative;
                z-index:1;
                overflow:hidden;
            ">
        </div>
    `);

    // -----------------------------------------
    // Leaflet CSS
    // -----------------------------------------

    if (!document.getElementById("employee-route-map-style-fix")) {

        const style = document.createElement("style");

        style.id = "employee-route-map-style-fix";

        style.innerHTML = `
            #employee_route_map .leaflet-pane,
            #employee_route_map .leaflet-top,
            #employee_route_map .leaflet-control {
                z-index: 2 !important;
            }

            #employee_route_map {
                isolation: isolate;
            }
        `;

        document.head.appendChild(style);
    }

    // -----------------------------------------
    // Check container
    // -----------------------------------------

    const container = document.getElementById("employee_route_map");

    if (!container) {
        console.error("Map container not found.");
        return;
    }

    // -----------------------------------------
    // Create Leaflet map
    // -----------------------------------------

    const map = L.map(container);

    frm.employee_route_map = map;

    // -----------------------------------------
    // OpenStreetMap
    // -----------------------------------------

    L.tileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19
        }
    ).addTo(map);

    // -----------------------------------------
    // Validate Employee and Time
    // -----------------------------------------

    if (!frm.doc.employee || !frm.doc.time) {

        console.log(
            "Employee or Checkin Time is missing.",
            frm.doc.employee,
            frm.doc.time
        );

        map.setView([20.5937, 78.9629], 5);

        return;
    }

    // -----------------------------------------
    // IMPORTANT:
    // Get DATE directly from Frappe.
    //
    // Do NOT use:
    // toISOString()
    // -----------------------------------------

    const checkinDate = frappe.datetime.obj_to_str(
        frappe.datetime.str_to_obj(frm.doc.time)
    ).split(" ")[0];

    console.log("Employee Checkin Time:", frm.doc.time);
    console.log("Route Date:", checkinDate);

    // -----------------------------------------
    // Get route
    // -----------------------------------------

    frappe.call({

        method: "jkmpcl_hr.py.employee_route.get_employee_route",

        args: {
            employee: frm.doc.employee,
            date: checkinDate
        },

        callback: function (r) {

            console.log("Employee Route Response:", r.message);

            const data = r.message;

            if (!data) {

                console.log("No route data found.");

                map.setView(
                    [20.5937, 78.9629],
                    5
                );

                return;
            }

            // -----------------------------------------
            // Distance
            // -----------------------------------------

            const distance = Number(
                data.total_distance || 0
            ).toFixed(2);

            if (
                Number(frm.doc.custom_distance_travelled_in_km || 0)
                !== Number(distance)
            ) {

                frm.set_value(
                    "custom_distance_travelled_in_km",
                    distance
                ).then(() => {

                    if (
                        !frm.is_new() &&
                        frm.dirty()
                    ) {
                        frm.save();
                    }

                });
            }

            // -----------------------------------------
            // Draw route
            // -----------------------------------------

            draw_route(
                map,
                data.start,
                data.route_points || [],
                data.activities || [],
                data.end
            );

            // -----------------------------------------
            // Fix Leaflet size after rendering
            // -----------------------------------------

            setTimeout(() => {

                if (frm.employee_route_map) {
                    frm.employee_route_map.invalidateSize();
                }

            }, 300);
        }
    });
}


function draw_route(
    map,
    start,
    route_points,
    activities,
    end
) {

    console.log("draw_route called");

    const latlngs = [];

    // -----------------------------------------
    // Route points
    // -----------------------------------------

    route_points.forEach(point => {

        if (
            !point.latitude ||
            !point.longitude
        ) {
            return;
        }

        latlngs.push([
            parseFloat(point.latitude),
            parseFloat(point.longitude)
        ]);
    });

    console.log("Start:", start);
    console.log("End:", end);

    // -----------------------------------------
    // Check-In
    // -----------------------------------------

    if (start) {

        const startLatLng = [
            parseFloat(start.latitude),
            parseFloat(start.longitude)
        ];

        L.circleMarker(
            startLatLng,
            {
                radius: 9,
                color: "green"
            }
        )
        .addTo(map)
        .bindPopup(`
            <b>🟢 Check-In</b><br>
            ${start.timestamp}
        `);
    }

    // -----------------------------------------
    // Activities
    // -----------------------------------------

    console.log("Activities:", activities);

    activities.forEach((activity, index) => {

        if (
            !activity.latitude ||
            !activity.longitude
        ) {
            return;
        }

        const latlng = [
            parseFloat(activity.latitude),
            parseFloat(activity.longitude)
        ];

        console.log(
            "Activity " + index,
            latlng
        );

        L.marker(latlng)
            .addTo(map)
            .bindPopup(`
                <b>${activity.purpose || ""}</b><br>
                ${activity.activity_details || ""}<br>
                📍 ${activity.custom_location || ""}<br>
                🕒 ${activity.request_date || ""}
            `);
    });

    // -----------------------------------------
    // Check-Out
    // -----------------------------------------

    if (end) {

        const endLatLng = [
            parseFloat(end.latitude),
            parseFloat(end.longitude)
        ];

        L.marker(
            endLatLng,
            {
                icon: redIcon
            }
        )
        .addTo(map)
        .bindPopup(`
            <b>🔴 Check-Out</b><br>
            ${end.timestamp}
        `);
    }

    // -----------------------------------------
    // Fit map
    // -----------------------------------------

    if (latlngs.length > 1) {

        L.polyline(
            latlngs,
            {
                color: "blue",
                weight: 5
            }
        ).addTo(map);

        map.fitBounds(latlngs);

    } else if (latlngs.length === 1) {

        map.setView(
            latlngs[0],
            15
        );

    } else if (start) {

        map.setView(
            [
                parseFloat(start.latitude),
                parseFloat(start.longitude)
            ],
            15
        );

    } else if (end) {

        map.setView(
            [
                parseFloat(end.latitude),
                parseFloat(end.longitude)
            ],
            15
        );
    }
}

function draw_route(map, start, route_points, activities, end) {
	console.log("draw_route called");

	console.table(route_points);

    const latlngs = [];

	route_points.forEach(point => {

		if (!point.latitude || !point.longitude) return;

		latlngs.push([
			parseFloat(point.latitude),
			parseFloat(point.longitude)
		]);

	});
	console.log("Start:", start);
	console.log("End:", end);

    if (start) {

        const startLatLng = [
            parseFloat(start.latitude),
            parseFloat(start.longitude)
        ];

        L.circleMarker(startLatLng, {
			radius: 9,
			color: "green"
		})
		.addTo(map)
		.bindPopup(`
			<b>🟢 Check-In</b><br>
			${start.timestamp}
		`);
    }
	console.log("Activities", activities);

    activities.forEach((activity, index) => {

		console.log("Activity " + index + ":", activity);

        const latlng = [
            parseFloat(activity.latitude),
            parseFloat(activity.longitude)
        ];

		console.log("Activity " + index + " LatLng:", latlng);

		console.log(
			"LatLngs after activity " + index,
			JSON.parse(JSON.stringify(latlngs))
		);

        L.marker(latlng)
            .addTo(map)
            .bindPopup(`
                <b>${activity.purpose}</b><br>
                ${activity.activity_details || ""}<br>
                📍 ${activity.custom_location || ""}<br>
                🕒 ${activity.request_date}
            `);

    });

    if (end) {

        const endLatLng = [
            parseFloat(end.latitude),
            parseFloat(end.longitude)
        ];

        L.marker(endLatLng, {
			icon: redIcon
		})
		.addTo(map)
		.bindPopup(`
			<b>🔴 Check-Out</b><br>
			${end.timestamp}
		`);
    }

    if (latlngs.length > 1) {

        L.polyline(latlngs, {
            color: "blue",
            weight: 5
        }).addTo(map);

        map.fitBounds(latlngs);

    } else if (latlngs.length === 1) {
        map.setView(latlngs[0], 15);
    }
}