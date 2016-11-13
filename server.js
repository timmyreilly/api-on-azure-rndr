#!/usr/bin/env node

//// Dependencies
var admin           = require("firebase-admin");
var serviceAccount  = require("./serviceAccountCredentials.json")
var express         = require('express')
var bodyParser      = require('body-parser')

var app = express()
app.use(bodyParser.json())

//// API Endpoints

/**
 * Create a post given a post object.
 * Verb: POST
 *
 * Post Object
 * - author <string>
 * - time <int>
 * - type <string> [text|image|video|gif|object]
 * - url <string>
 * - location <Array of 2 floats>
 * - marker <string> (an url)
 */
app.post('/post', function(req, res) {
  req.body['time'] = Date.now()
  writePost(req.body)
  res.send('Ok')
});

/**
 * Return a list of posts given a latitude and longitude.
 * Verb: GET
 */
app.get('/posts/:lat/:lon', function(req, res) {
  var location = req.params
  var locationObject = [location.lat, location.lon]

  // Query posts by location
  var listOfNearbyPostObjects = []
  getNearbyPosts(locationObject).then(function(data) {
    listOfNearbyPostObjects = data
    res.send(listOfNearbyPostObjects)
  }, function(err) {
    res.status(400)
    console.log("Error:", err)
    res.send(listOfNearbyPostObjects)
  })

})

var port = process.env.PORT || 5000
app.listen(port, function() {
  console.log('Running on port 5000. Press <Ctrl + C> to quit.')
})

//// Database Interaction

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://rndr-77d10.firebaseio.com"
})

var __database = admin.database()
function getDatabaseReference() {
  return __database.ref()
}

function writePost(postObject) {
  var ref = getDatabaseReference()
  ref.child('posts').push(postObject)
}

function getNearbyPosts(locationData) {
  var promise = new Promise(function(resolve, reject) {
    getRadiusInFeet().then(function(radiusFt) {
      console.log('got radius', radiusFt)

      var ref = getDatabaseReference()
      ref.child('posts').once("value", function(snapshot) {
        // Filter each snapshot by distance.
        // Super inefficient for now. Should use GeoFire (which)
        // didn't work.
        var data = []
        snapshot.forEach(function(snaps) {
          var obj = snaps.val()
          var dist = Math.abs(distanceInFeet(locationData, obj['location']))
          console.log(snaps.key, 'distance', dist)
          if (dist <= radiusFt) {
            obj['id'] = snaps.key
            data.push(obj)
          }
        })

        resolve(data)
      }, function (errorObject) {
        reject('Error')
      })
    })
  })
  return promise
}

function getRadiusInFeet() {
    var promise = new Promise(function(resolve, reject) {
      var ref = getDatabaseReference()
      ref.child('constants').once("value", function(snapshot) {
        resolve(snapshot.val()["RADIUS_IN_FT"])
      }, function (errorObject) {
        reject('Error retrieving radius in feet.')
      })
    })

    return promise
}

//// Utilities

// Source: http://www.movable-type.co.uk/scripts/latlong.html
function distanceInFeet(point1, point2) {
  var lat1 = point1[0];
  var lon1 = point1[1];
  var lat2 = point2[0];
  var lon2 = point2[1];
  var R = 6371e3; // metres
  var φ1 = lat1 * (Math.PI/180);
  var φ2 = lat2 * (Math.PI/180);
  var Δφ = (lat2-lat1) * (Math.PI/180);
  var Δλ = (lon2-lon1) * (Math.PI/180);

  var a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
          Math.cos(φ1) * Math.cos(φ2) *
          Math.sin(Δλ/2) * Math.sin(Δλ/2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  var d = R * c;

  var FEET_KM_CONSTANT = 3.280839895;
  return d * FEET_KM_CONSTANT;
}
