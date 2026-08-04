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
        render_map(frm);
    }
});

function render_map(frm) {

    const field = frm.fields_dict.custom_route_map;

    if (!field) {
        console.error("HTML field 'custom_route_map' not found.");
        return;
    }

    // Create map container
    field.$wrapper.html(`
        <div id="employee_route_map"
             style="height:500px;width:100%;border-radius:8px;margin-bottom:10px;border:1px solid #ccc;">
        </div>
    `);

    // Destroy previous map instance if the form refreshes
    const container = L.DomUtil.get("employee_route_map");

    if (container && container._leaflet_id) {
        container._leaflet_id = null;
    }

    // Create map
    const map = L.map("employee_route_map");

    // OpenStreetMap Tiles
    L.tileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19
        }
    ).addTo(map);

    // --------------------------
    // Lat Long API Response Data
    // --------------------------

    frappe.call({
		method: "jkmpcl_hr.py.employee_route.get_employee_route",
		args: {
			employee: frm.doc.employee,
			date: frappe.datetime.str_to_obj(frm.doc.time)
				.toISOString()
				.slice(0, 10)
		},
		callback: function (r) {

			const data = r.message;

			if (!data) {
				frappe.msgprint("No route data found.");
				return;
			}

			const distance = Number(data.total_distance || 0).toFixed(2);

			if (frm.doc.custom_distance_travelled_in_km != distance) {

				frm.set_value("custom_distance_travelled_in_km", distance)
					.then(() => {
						if (!frm.is_new()) {
							frm.save();
						}
					});

			}

			draw_route(map, data.start, data.route_points, data.activities, data.end);
		}
	});
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