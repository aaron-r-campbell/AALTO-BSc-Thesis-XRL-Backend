# Standard library imports
import os

# Third-party library imports
from bs4 import BeautifulSoup
from flask import (
    abort,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from functools import wraps
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import (
    urlparse,
    urljoin,
)

### GLOBAL ATTRIBUTES ###

CUSTOM_SITES = {
    1: "https://www.aalto.fi",
    2: "https://en.wikipedia.org/wiki/Aalto_University",
    3: "https://github.com/aaron-r-campbell",
}

DRIVER = None

XRL_CLASSES = [
    'XRL-main',
    'XRL-head',
    'XRL-below',
    'XRL-right',
    'XRL-left',
    'XRL-ignore',
    'XRL-element',
]

### FLASK APP ###

app = Flask(__name__)
app.url_map.strict_slashes = False


### WRAPPERS ###


def validate_custom_num(func):
    @wraps(func)
    def wrapper(num):
        """
        A wrapper function that validates the input number is in the list of custom sites.

        Args:
            num: The input number to be validated.

        Returns:
            The result of the input function if num is in CUSTOM_SITES, otherwise aborts with 404 error.
        """
        return func(num) if num in CUSTOM_SITES else abort(404)
    return wrapper

### FLASK ROUTES ###


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('./examples', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    """
    This function generates the endpoints dictionary and renders the HTML template for the index page.

    Returns:
        str: The HTML for the index page.
    """
    return render_template(
        'endpoints.html',
        base_url=request.base_url,
        endpoints=[
            ['',
             '/',
             'Page providing an overview of different app routes'],
            ['info',
             '/<name>',
             'Serves example site from \'examples\' folder'],
            ['custom/1',
             '/custom/<int:num>',
             'Redirects to custom route number \'num\' (out of 3)'],
            [f'custom/1?url={CUSTOM_SITES[1]}',
             '/custom/<int:num>',
             'Updates routing for custom site number \'num\' (out of 3)'],
            [f'xrl?url={request.base_url}/info',
             '/xrl?url=<url>',
             'Serves an emulated XRL layout for a given link'],
            [f'render?url={request.base_url}/info',
             '/render?url=<url>',
             'Render elements as images from a webpage using the given url'],
            ['images/full_page.png',
             '/images/<filename>',
            'Get an image by filename'],
             ['routes',
              '/routes',
              'Serves JSON detailing available example and custom site links'],
        ],
        example_sites=[
            [
                site,
                f'{site}',
                f'xrl?url={request.base_url}/{site}',
            ] for site in sorted(get_example_sites())
        ],
        custom_sites=[
            [
                CUSTOM_SITES[site],
                f'custom/{i+1}',
                f'xrl?url={CUSTOM_SITES[site]}',
            ] for i, site in enumerate(CUSTOM_SITES)
        ],
    )


@app.route('/routes')
def route_info():
    """
    Returns json containing available site routes.
    """
    base_url = request.base_url
    example_sites = [{'name': name, 'url': urljoin(
        base_url, name)} for name in sorted(get_example_sites())]
    custom_sites = [{'name': f'custom-{num}',
                     'url': urljoin(base_url, f'custom/{num}')} for num in CUSTOM_SITES]
    return jsonify({'example_sites': example_sites, 'custom_sites': custom_sites})


@app.route('/<name>')
def serve_static(name):
    """
    Serve static files, example sites, or custom sites based on the provided `name`.

    Args:
        name (str): The name of the file or site to serve.

    Returns:
        A Flask `Response` object with the contents of the requested file or site, or a redirect
        to a custom site if the name is an integer between 0 and 2 (inclusive), or a 404 error if
        the requested resource doesn't exist.

    """
    # Serve static files
    static_files = {
        "style.css": "text/css",
        "thesis.js": "text/javascript"
    }
    if name in static_files:
        return send_from_directory('./examples', name, mimetype=static_files[name])

    # Serve example sites
    if name in get_example_sites():
        return send_from_directory('./examples', f"{name}.html")

    # Serve custom sites
    try:
        num = int(name)
        if num not in range(len(CUSTOM_SITES)):
            return "Custom site out of bounds", 500
        return redirect(CUSTOM_SITES[num], code=302)
    except ValueError:
        pass

    # Page not found
    return abort(404)


@app.route('/xrl')
def xrl():
    """Renders an XR page based on the provided URL.

    Returns:
        str: The rendered template as a string.

    Raises:
        BadRequest: If URL parameter is missing in the request.
    """

    # Get the URL parameter from the request
    url = request.args.get('url')

    if not url:
        # Return a 400 Bad Request error if the URL parameter is missing
        abort(400, 'URL parameter is missing.')

    # Pre-process any redirects and get the final url
    new_url = requests.get(url).url
    if new_url != url:
        return redirect(f'{request.base_url}?url={new_url}')

    # Call the render_xrl function to extract elements from the URL and render the template
    return render_template('xrl_emulator.html', **render_xrl(url))


@app.route('/render')
def render():
    """
    Renders images of an XRL page based on the provided URL.

    Returns:
    - A JSON object representing the rendered version of the webpage.

    Raises:
        BadRequest: If URL parameter is missing in the request.
    """
    # Create images folder if its missing
    import os; os.makedirs('images', exist_ok=True)

    # Get the URL parameter from the request
    url = request.args.get('url')

    if not url:
        # Return a 400 Bad Request error if the URL parameter is missing
        abort(400, 'URL parameter is missing.')

    # Pre-process any redirects and get the final url
    new_url = requests.get(url).url
    if new_url != url:
        return redirect(f'{request.base_url}?url={new_url}')

    # Render the page using the URL
    base_url = request.base_url.replace('/render', '')
    return jsonify(render_page(f'{base_url}/xrl?url={url}', base_url))


@app.route('/images/<filename>')
def get_image(filename):
    """
    This function routes incoming requests for a specific image to the server and returns the image file as a response.

    Parameters:
    image (str): The name of the image file to retrieve.

    Returns:
    A file object containing the specified image file.

    Raises:
    If the specified image file does not exist in the image directory, a 404 error is raised.
    """
    # Create images folder if its missing
    import os; os.makedirs('images', exist_ok=True)
    
    return send_from_directory('./images', filename, mimetype='image/jpeg')


@app.route('/custom/<int:num>')
@validate_custom_num
def custom(num):
    """
    This function updates or redirects to a custom URL based on the given custom number.

    Args:
        num (int): The custom number to update or redirect to.

    Returns:
        str: A message confirming the update or redirect.
        HTTP status code 200 if an update was made, otherwise a redirect with status code 302.
    """
    # Get the URL from the request arguments.
    url = request.args.get('url')

    # If a URL was provided, update the custom site with the given number.
    if url:
        CUSTOM_SITES[num] = url
        return f'Site {num} updated to {url}', 200

    # Otherwise, redirect to the custom site with the given number.
    return redirect(CUSTOM_SITES[num], code=302)

### HELPER FUNCTIONS ###


def get_example_sites():
    """
    This function retrieves a list of files in the './examples' directory that end
    with the extension '.html', and removes the extension from the filenames to
    obtain the site names. The resulting list of site names is returned.

    Returns:
        A list of example site names as strings.
    """
    # Get a list of files in the './examples' directory that end with '.html'
    html_files = [file for file in os.listdir(
        './examples') if file.endswith('.html')]

    # Remove the '.html' extension from each filename to obtain the site name
    site_names = [os.path.splitext(file)[0] for file in html_files]

    return site_names


def initialize_driver():
    """
    Initializes a global WebDriver object for Firefox browser, sets the browser window size, and enables headless mode.
    """
    global DRIVER

    # create a ChromiumOptions object
    options = webdriver.ChromeOptions()

    # add the '--headless' argument to run the browser in headless mode
    options.add_argument('--headless')

    # create a WebDriver object for Chromium with the specified options
    DRIVER = webdriver.Chrome(options=options)

    # set the browser window size to 2000 x 6000 pixels
    DRIVER.set_window_size(2000, 6000)

    print('initialized driver')


def hide_other_elements(driver, element) -> None:
    """
    Hide all elements except for the specified element and its ancestors.
    Then hide all elements with the specified XRL classes.

    Args:
        driver: The WebDriver instance to use.
        element: The element to keep visible, along with its ancestors.
        xrl_classes: The list of classes to hide.

    Returns:
        None
    """
    # Find all elements to keep visible, i.e. the specified element and its ancestors
    exclusion_pattern = "*[not(self::script or self::style or self::head or self::meta)]"
    elements_to_show = element.find_elements(
        By.XPATH, f".//{exclusion_pattern} | ./ancestor::{exclusion_pattern}")

    # Show all elements to keep visible
    driver.execute_script("""
        var elements = arguments[0];
        for (var el of elements) {
            try {
                var style = el.style;
                style.visibility = 'visible';
                style.display = style.diplay == 'none' ? 'flex' : style.display;
            } catch (e) { };
        }
    """, list(elements_to_show))

    # Find all elements with the specified XRL classes
    elements_to_hide = element.find_elements(
        By.CSS_SELECTOR, f".{', .'.join(XRL_CLASSES)}")

    # Hide all elements with the specified XRL classes
    driver.execute_script("""
        var elements = arguments[0];
        for (var i = 0; i < elements.length; i++) {
            try {
                elements[i].style.visibility = 'hidden';
                elements[i].style.display = 'none';
            } catch (e) { };
        }
    """, elements_to_hide)


def render_page(url: str, base_url: str) -> dict:
    """
    Takes a URL as input and returns a dictionary of image data for various elements of the webpage.

    Args:
        url (str): The URL of the webpage to be rendered.

    Returns:
        dict: A dictionary of image data for various elements of the webpage.
              The keys of the dictionary are 'XRL_head', 'XRL_left', 'XRL_right', 'XRL_main', 'XRL_below', and 'full_page'.
              The value of each key is a list of dictionaries containing 'url', 'width', and 'height' keys.
    """
    # check if DRIVER exists, initialize it if it does not exist
    if not DRIVER:
        initialize_driver()

    # navigate to the given URL
    DRIVER.get(url)

    # execute JavaScript to show any hidden elements and set maximum width for elements with class 'XRL-container'
    DRIVER.execute_script("""
        document.body.style.transform = "scale(1)";
        document.body.style.transformOrigin = "0 0";
        document.querySelectorAll(".XRL-container").forEach((container) => {
            container.style.maxWidth = "none";
        });
        const elementsToUpdate = new Set();

        document.querySelectorAll('.XRL-head, .XRL-left, .XRL-right, .XRL-main, .XRL-below').forEach(element => {
            const elementStyle = window.getComputedStyle(element);

            if (element.offsetWidth === 0 || element.offsetHeight === 0 || elementStyle.visibility === 'hidden') {
                let parent = element.parentElement;
                while (parent) {
                if (!elementsToUpdate.has(parent)) {
                    const parentStyle = window.getComputedStyle(parent);
                    if (parent.offsetWidth === 0 || parent.offsetHeight === 0 || parentStyle.visibility === 'hidden') {
                    elementsToUpdate.add(parent);
                    }
                }
                parent = parent.parentElement;
                }
                if (!elementsToUpdate.has(element)) {
                elementsToUpdate.add(element);
                }
            }
        });

        elementsToUpdate.forEach(element => {
            element.style.display = 'flex';
            element.style.visibility = 'visible';
        });
    """)

    # set maximum width and height for all elements with class 'XRL-container'
    for el in DRIVER.find_elements(By.CLASS_NAME, 'XRL-container'):
        DRIVER.execute_script(
            "arguments[0].style.maxWidth='none';arguments[0].style.maxHeight='none';", el)

    # find all elements with class 'XRL-main' and split them into two parts: the first part and the rest
    main_list = DRIVER.find_elements(By.CLASS_NAME, 'XRL-main')
    data = {
        'XRL_head': DRIVER.find_elements(By.CLASS_NAME, 'XRL-head'),
        'XRL_left': DRIVER.find_elements(By.CLASS_NAME, 'XRL-left'),
        'XRL_right': DRIVER.find_elements(By.CLASS_NAME, 'XRL-right'),
        'XRL_main': main_list[:1],
        'XRL_below': main_list[1:] + DRIVER.find_elements(By.CLASS_NAME, 'XRL-below'),
    }

    # Find the full page element
    full_page = DRIVER.find_element(By.TAG_NAME, 'body')

    # Take a screenshot of the full page
    full_page.screenshot(f'images/full_page.png')

    # Store the screenshot data in a dictionary
    image_data = {
        'full_page': {
            'url': f'{base_url}/images/full_page.png',
            **full_page.size,
        }
    }

    # Iterate over the data items
    for key, value in data.items():
        # Create an empty list to store the screenshot data for this item
        image_data[key] = []

        # Iterate over the elements for this item
        for i, element in enumerate(value):
            # Hide other elements on the page to isolate the target element
            hide_other_elements(DRIVER, element)

            # Check that the element has non-zero width and height
            if element.size['width'] != 0 and element.size['height'] != 0:
                # Take a screenshot of the element
                element.screenshot(f'images/{key}-{i}.png')

                # Store the screenshot data in the list for this item
                image_data[key].append({
                    'url': f'{base_url}/images/{key}-{i}.png',
                    **element.size,
                })

    return image_data


def render_xrl(url: str) -> str:
    """
    Load the HTML content of a given URL, parse it using BeautifulSoup, and prepare the page
    for XRL (Extended Reading List) view. This involves setting the page title, adding a
    <base> tag to the <head> section with the specified URL, fixing all external resource
    links to work with XRL view, and extracting content according to XRL framework classes.

    Args:
        url (str): The URL to load and render.

    Returns:
        dict: A dictionary with the following keys and values:
            - 'xrl_main': a list with one element, representing the main content of the page
              formatted for XRL view
            - 'xrl_head': a list of elements to be displayed in the XRL header
            - 'xrl_below': a list of elements to be displayed below the XRL main content
            - 'xrl_right': a list of elements to be displayed in the XRL right sidebar
            - 'xrl_left': a list of elements to be displayed in the XRL left sidebar
            - 'head_list': a list of elements to be displayed in the HTML <head> section
            - 'footer_list': a list of elements to be displayed in the HTML footer section
            - 'style_list': a list of <link> elements referencing external stylesheets
            - 'script_list': a list of <script> elements referencing external scripts
    """

    def fix_link(link: str, base_url: str) -> str:
        """
        Helper function which returns the absolute URL of a given link by adding the domain if needed

        Args:
            link (str): The URL to fix.
            base_url (str): The base URL to use as the reference.

        Returns:
            str: The absolute URL.
        """
        # If the link is not relative, return the link
        if urlparse(link).netloc:
            return link

        # Join the base URL with the relative link to get the absolute URL
        return urljoin(f"{base_url}", link)

    # Add http if http/https not present
    url = url if url.startswith('http') else f'http://{url}'

    # Get the HTML content of the URL and parse it using BeautifulSoup
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')

    # Set the XRL View page title to the original page title, or to 'XRL View' if there is no title
    soup.title.string = f'XRL View - {soup.title.string}' if soup.title else 'XRL View'

    # Add a <base> tag to the <head> section of the HTML with the specified URL
    (soup.find('head') or soup.new_tag('head')).insert(
        0, soup.new_tag('base', href=url))

    # Fix all external resource links to work with the XRL View
    for tag in soup.find_all(['script', 'link', 'img', 'meta']):
        if tag.has_attr('src'):
            tag['src'] = fix_link(tag['src'], url)
        elif tag.has_attr('href'):
            tag['href'] = fix_link(tag['href'], url)
        elif tag.has_attr('content') and tag['content'] and tag.get('itemprop') == 'image':
            tag['content'] = fix_link(tag['content'], url)

    # Create XRL content lists
    xrl_ignore = [element.extract()
                  for element in soup.find_all(class_='XRL-ignore')]
    xrl_head = [element.extract()
                for element in soup.find_all(class_='XRL-head')]
    xrl_left = [element.extract()
                for element in soup.find_all(class_='XRL-left')]
    xrl_right = [element.extract()
                 for element in soup.find_all(class_='XRL-right')]
    xrl_main = [element.extract()
                for element in soup.find_all(class_='XRL-main')]
    xrl_below = [element.extract()
                 for element in soup.find_all(class_='XRL-below')]

    # Create a wrapper element to store content which doesn't implement the XRL framework
    legacy_content = soup.new_tag(
        'div', attrs={'class': 'XRL-below', 'id': 'XRL-computed-legacy'})
    legacy_content.append(soup)

    # Create supporting lists
    head_list = [element.extract() for element in soup.find_all('head')]
    footer_list = [element.extract() for element in soup.find_all('footer')]
    script_list = [element.extract() for element in soup.find_all('script')]
    style_list = []
    for element in soup.find_all('link'):
        if element.has_attr('rel') and 'stylesheet' in element['rel']:
            style_list.append(element.extract())
        else:
            head_list.append(element.extract())

    return {
        'xrl_main': xrl_main[:1],
        'xrl_head': xrl_head,
        'xrl_below': xrl_main[1:] + xrl_below + [legacy_content],
        'xrl_right': xrl_right,
        'xrl_left': xrl_left,
        'head_list': head_list,
        'footer_list': footer_list,
        'style_list': style_list,
        'script_list': script_list
    }


### MAIN ###

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
