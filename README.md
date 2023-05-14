# XRL Backend

This python app contains example sites and a demo XRL browser emulator as well as acting as a backend for the companion Oculus VR demo application. The app is build using [Flask](https://flask.palletsprojects.com) as well as using the [selenium webdriver](https://www.selenium.dev/). This readme contains a userguide and general project overview.

## Running the App

### Running with Docker

To run the app from Docker, please follow the steps below:

1. Clone this repository
2. Build the Docker image using the Dockerfile provided: 
```sh
docker build -t <image_name> .
```
3. Run the Docker container:
```sh
docker run -p <host_port>:5000 -it <image_name>
```

Make sure to replace `<image_name>` with a name of your choice and `<host_port>` with the desired local port number (5000 is reccomended if available).

### Running Locally

To run the app locally, please follow the steps below:

1. Clone this repository
2. Install the required packages:
```sh
pip install -r requirements.txt
```
3. Install the Google Chrome browser from from the following link:

   * [Chrome Browser](https://www.google.com/chrome/)

4. Download the latest version of Chrome WebDriver from the following link:
   
   * [Chrome WebDriver](https://chromedriver.chromium.org/downloads)

   Make sure you download the version that matches your Chrome browser version. You can check your Chrome browser version by navigating to `chrome://settings/help` in your browser.

5. Extract the downloaded ZIP file and move the `chromedriver` executable to a directory on your system's PATH. This allows you to run `chromedriver` from any location on your system.
6. Run the app:
```sh
python app.py
```

The app should now be running on `http://localhost:5000`.

## Current Functionality

The following routes are currently available in this Flask app:

- `/`: Page providing an overview of different app routes
- `/<name>`: Serves example site from `examples` folder
- `/custom/<int:num>`: Redirects to custom route number `num` (out of 3)
- `/custom/<int:num>?url=<url>`: Updates routing for custom site number `num` (out of 3)
- `/xrl?url=<url>`: Serves an emulated XRL layout for a given link
- `/render?url=<url>`: Render elements as images from a webpage using the given url
- `/images/<filename>`: Get an image by filename
- `/routes`: Serves JSON detailing available example and custom site links

## Known Issues

- When rendering the XRL layout of a compatible site, occasionally there is some detected `remainder` content which consists solely of CSS padding. This appears most noticeably in the Oculus XRL Browser Demo as a blank frame at the bottom of the XRL-below path.
- xrl and render paths are currently slower than they ideally should be.

## Next Steps

The following are the next steps for this Flask app project:

- Improve xrl and render path loading times.

## Additional Information

Created by [Aaron Campbell](https://github.com/aaron-r-campbell) as part of a BSc at [Aalto University](https://www.aalto.fi).