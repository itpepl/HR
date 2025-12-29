// frappe.ui.form.on("Branch", {
//     refresh(frm) {
//         draw_geofence(frm);
//     },
//     custom_latitudes_and_longitudes(frm) {
//         draw_geofence(frm);
//     }
// });

// function draw_geofence(frm) {
//     if (!frm.doc.custom_latitudes_and_longitudes) return;
//     if (!frm.fields_dict.custom_map) return;  

//     let map_field = frm.fields_dict.custom_map;
//     let map = map_field.map;

//     if (!map) {
//         setTimeout(() => draw_geofence(frm), 500);
//         return;
//     }

//     map.eachLayer(layer => {
//         if (layer instanceof L.Polygon) {
//             map.removeLayer(layer);
//         }
//     });

//     let matches = frm.doc.custom_latitudes_and_longitudes.match(
//         /(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)/g
//     );

//     if (!matches || matches.length < 3) return;

//     let polygon = matches.map(row => {
//         let parts = row.split(",");
//         return [parseFloat(parts[0]), parseFloat(parts[1])];
//     });

//     // Draw polygon
//     let poly = L.polygon(polygon, {
//         color: "red",
//         weight: 3,
//         fillColor: "#3388ff",
//         fillOpacity: 0.4
//     }).addTo(map);

//     // Fit map to polygon
//     map.fitBounds(poly.getBounds());
// }
