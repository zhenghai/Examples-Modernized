// Disable Cesium Ion token usage
Cesium.Ion.defaultAccessToken = null;


// Create Cesium viewer

const viewer =
    new Cesium.Viewer(
        "cesiumContainer",
        {
            animation: false,
            timeline: false,

            baseLayerPicker: false,
            geocoder: false,
            homeButton: false,
            sceneModePicker: false,
            navigationHelpButton: false,
            fullscreenButton: false,

            infoBox: false,
            selectionIndicator: false,

            terrainProvider:
                new Cesium.EllipsoidTerrainProvider()
        }
    );


// Remove default imagery

viewer.imageryLayers.removeAll();


// Add OpenStreetMap imagery

viewer.imageryLayers.addImageryProvider(
    new Cesium.OpenStreetMapImageryProvider({

        url:
            "https://tile.openstreetmap.org/"

    })
);


// Zoom to USA

viewer.camera.flyTo({

    destination:
        Cesium.Cartesian3.fromDegrees(
            -98,
            39,
            3000000
        )

});



const info =
    document.getElementById("details");



// Load bank data

fetch("bank_failures.json")

.then(response => response.json())

.then(data => {


    data.forEach(yearGroup => {


        const year =
            yearGroup[0];


        const banks =
            yearGroup[1];



        banks.forEach(bank => {



            const name =
                bank[0];


            const city =
                bank[1];


            const state =
                bank[2];


            const date =
                bank[3];


            const buyer =
                bank[4];


            // Remove commas from values like "2,700"

            const assets =
                Number(
                    String(bank[5])
                    .replace(/,/g, "")
                );


            const latitude =
                Number(bank[6]);


            const longitude =
                Number(bank[7]);



            if (

                !Number.isFinite(latitude) ||

                !Number.isFinite(longitude) ||

                !Number.isFinite(assets)

            ) {

                console.warn(
                    "Skipping bad record:",
                    bank
                );

                return;

            }



            const height =
                Math.min(
                    assets * 10000,
                    500000
                );



            viewer.entities.add({

                name: name,


                position:
                    Cesium.Cartesian3.fromDegrees(
                        longitude,
                        latitude,
                        0
                    ),



                polyline: {

                    positions: [

                        Cesium.Cartesian3.fromDegrees(
                            longitude,
                            latitude,
                            0
                        ),

                        Cesium.Cartesian3.fromDegrees(
                            longitude,
                            latitude,
                            height
                        )

                    ],

                    width: 5,

                    material:
                        Cesium.Color.RED

                },



                properties: {

                    bank: name,
                    city: city,
                    state: state,
                    date: date,
                    buyer: buyer,
                    assets: assets,
                    year: year

                }

            });


        });


    });



    viewer.zoomTo(
        viewer.entities
    );


})

.catch(error => {

    console.error(
        "Error loading bank data:",
        error
    );

});





// Hover information

const handler =
    new Cesium.ScreenSpaceEventHandler(
        viewer.scene.canvas
    );


handler.setInputAction(

function(movement) {


    const picked =
        viewer.scene.pick(
            movement.endPosition
        );


    if (

        Cesium.defined(picked) &&

        picked.id &&

        picked.id.properties

    ) {


        const p =
            picked.id.properties;



        info.innerHTML =

        `
        <b>${p.bank.getValue()}</b><br><br>

        Year:
        ${p.year.getValue()}<br>

        Date:
        ${p.date.getValue()}<br>

        Location:
        ${p.city.getValue()},
        ${p.state.getValue()}<br>

        Buyer:
        ${p.buyer.getValue()}<br>

        Assets:
        $${p.assets.getValue().toLocaleString()} million
        `;


    }

    else {

        info.innerHTML =
            "Hover over a bar";

    }


},

Cesium.ScreenSpaceEventType.MOUSE_MOVE

);
