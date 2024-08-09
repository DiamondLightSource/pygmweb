# PyGMweb: An Online Visualisation Tool for the Plane Grating Monochromator

PyGMweb is an online Shiny dashboard app which can simulate the geometry of a plane grating monochromator quickly and easily.
A static set of files containing the necessary python environment in webassembly is located in the `site` directory.

The main web app can be found at [pgmweb.diamond.ac.uk](https://pgmweb.diamond.ac.uk). Should you wish to run the app yourself locally, you can do so by following the steps:
1. Clone this repository and cd into it.
2. Issue the command `python3 -m http.server --directory app --bind localhost 8008` to start a HTTP server using python.
3. Using a web browser of your choice, go to localhost:8008 to access the web interface.
   
