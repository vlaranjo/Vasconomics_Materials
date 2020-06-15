from IPython.core.display import display, HTML, Javascript

import json
import pandas as pd

LAST_ID = 1


class Raw(str):
    """Raw javascript code (not quoted by to_js)"""
    pass


def __process_data(df, cols, process_func):
    if cols and isinstance(cols, list):
        df = df[cols]
    if process_func and callable(process_func):
        return process_func(df)
    return df


def from_csv(filename, sep=',', columns=None, process_func=None):
    """Read data from a csv file

    Args:
        filename: path to a csv file
        sep (str, optional): delimiter, default is ','
        columns (list, optional): list of columns to keep. All columns are kept by default
        process_func (function, optional): A callable object that you can pass to process you data in a specific way

    Returns:
        pandas.DataFrame: return a dataframe object
    """
    df = pd.read_csv(filename, sep=sep)
    return __process_data(df, columns, process_func)


def from_json(filename, columns=None, process_func=None):
    """Read data from a json file

    Args:
        filename: path to a json file
        columns (list, optional): list of columns to keep. All columns are kept by default
        process_func (function, optional): A callable object that you can pass to process you data in a specific way

    Returns:
        pandas.DataFrame: return a dataframe object
    """
    df = pd.read_json(filename)
    return __process_data(df, columns, process_func)


def to_js(indata):
    """Convert a python type to javascript (represented as a string)"""
    if indata is None:
        return ""
    if isinstance(indata, str):
        return "'{}'".format(indata)
    if isinstance(indata, list):
        return "[" + ",".join(to_js(x) for x in indata) + "]"
    if type(indata) == bool:
        return "{}".format(indata).lower()
    if type(indata) in [float, int]:
        return "{}".format(indata)
    if isinstance(indata, dict):
        return "{" + ",".join(to_js(k) + ": " + to_js(v) for k, v in indata.items()) + "}"
    elif isinstance(indata, Raw):
        return str(indata)
    else:
        raise ValueError(
            """Cannot convert object to Javascript. Unsupported format""")


class PyD3Plus(object):

    JS_LIBS = ['//d3plus.org/js/d3.js',
               '//d3plus.org/js/d3plus.js']

    def __init__(self, container_id='', height=400, width=500, **kwargs):
        """PyD3Plus is the Base class that defines all global visualization parameters.
        It cannot plot data !

        Args:
            container_id (None, optional): ID of the div where the viz should be attached
            height (int, optional): height of the container
            width (int, optional): width of the container
            **kwargs: Any additional keyword argument you pass
        """
        global LAST_ID
        if container_id:
            self.container_id = container_id
        else:
            self.container_id = "d3viz_{}".format(LAST_ID)
            LAST_ID += 1
        self.height = height
        self.width = width
        self.css = ""
        self.js = ""
        self._create_container()

    def setCSS(self, css):
        """Set personalized css code

        Args:
            css (str): File or String that contains any additional css you would like to add
        """
        try:
            val = open(css).read()
            css = val
        except:
            pass
        self.css = css.strip().lstrip('<style>').rstrip('</style>')

    def setJS(self, js):
        """Set personalized js code

        Args:
            js (str): File or String that contains any additional js code you would like to add
        """
        try:
            val = open(js).read()
            js = val
        except:
            pass
        self.js = js.strip().lstrip('<style>').rstrip('</style>')

    def _create_container(self):
        """Create and display the container"""
        container = """<div id='{cont}' style='height:{height}px;width:{width}px'></div>"""\
            .format(cont=self.container_id, height=self.height, width=self.width)
        display(HTML(container))

    def format_data(self, data):
        """Process data in a format recognizable in Javascript

        Args:
            data (data object): either a dataframe object or data in json encoded as string.
            Alternatively, a list of dict is also accepted.

        Returns: json formatted data
        """
        if type(data) == pd.DataFrame:
            return data.to_json(orient='records')
        elif isinstance(data, list) and len(data) > 0 and type(data[0]) == dict:
            return json.dumps(data)
        elif isinstance(data, str):
            return data
        else:
            raise ValueError("Cannot handle your input data")

    def draw(self, data):
        """Draw a visualization in the ipython notebook."""
        json_data = self.format_data(data)
        display(self.generate_js(json_data))

    def dump_html(self, data, container_id=None):
        """Dump a single-file self-contained html string designed to be loaded
        up into the browser on its own or embedded in a page."""
        json_data = self.format_data(data)

        html_template = """
        {scripts}
        <div id='{container_id}'></div>
        <style>
        div#{container_id}{{
             width: {w}px;
             height: {h}px;
        }}
        {css}
        </style>
        <script>
            {code}
        </script>
        """
        script_template = "<script src='{src}' type='text/javascript'></script>"
        scripts = "\n\t".join([script_template.format(src=x)
                               for x in self.JS_LIBS])
        code = self.generate_js(json_data).data
        if container_id:
            code = code.replace('#{}'.format(
                self.container_id), '#{}'.format(container_id))

        return html_template.format(container_id=(container_id or self.container_id), w=self.width,
                                    h=self.height, scripts=scripts, css=self.css, code=code)

    def generate_js(self, json_data):
        raise NotImplementedError()


class Plot(PyD3Plus):

    def __init__(self, id='id', x='x', y='y', ptype='line', text=None, color=None, tooltip=None, legend=None,  **kwargs):
        """Base class for most D3plus Plot (scatter/bar/box/stacked area/pie chart).
          It accepts all valid D3Plus parameters. Javascript Object type should be 
          represented as dict and Arrays as list.

        Args:
            id (str/object):  D3Plus id parameter, should be unique for each point
            x (str/object): D3Plus x parameter/key corresponding to the x axis in the json data, default: "x"
            y (str/object): D3Plus y parameter/key corresponding y axis variable in the json data, default: "y"
            ptype (str, optional): D3Plus plot type
            text (str, optional): D3Plus text parameter
            color (str, optional): D3Plus color parameter
            tooltip (list/str, optional): D3Plus tooltip parameter
            legend (boolean/object, optional): D3Plus tooltip parameter
            **kwargs: All remaning D3plus parameters
        """
        super(Plot, self).__init__(**kwargs)
        self.id = id or 'id'
        self.x = x
        self.y = y
        self.type = ptype
        self.text = (text or self.id)
        self.color = (color or self.id)
        self.tooltip = tooltip
        self.legend = legend
        self.__dict__.update(kwargs)  # yeah, i dont have trust issue

    def _format_params(self, dt=None):
        """Format parameters into valid javascript code"""
        params = []
        if dt is None or not isinstance(dt, dict):
            dt = self.__dict__.items()
        for k, v in dt:
            if k not in ['container_id', 'width', 'height', 'type', 'js', 'css', 'type', 'JS_LIBS'] and v is not None:
                params.append(".{key}({val})".format(key=k, val=to_js(v)))
        return Raw("\n\t\t".join(params))

    def generate_js(self, json_data):
        """Generate the javascript code to plot the data

        Args:
            json_data (dataframe, json string, list of dict): input data, will be automatically formatted as json. 

        Returns: the javascript code
        """
        js = """
        (function (){{
            {supjs}
            var viz_data = {viz_data};

            var viz_{viz_name} = d3plus.viz()
                .container({container})
                .type({type})
                {dtformat}
                .data(viz_data)
                .draw();

        }})();
        """.format(
            supjs=Raw(self.js),
            viz_data=json_data,
            viz_name=self.container_id,
            container=to_js("#" + self.container_id),
            type=to_js(self.type),
            dtformat=self._format_params()
        )
        return Javascript(lib=self.JS_LIBS, data=js, css=self.css)


class LinePlot(Plot):

    def __init__(self, id, x, y, **kwargs):
        """Plot a line plot.
        This is just syntactic sugar for Plot(id, x, y, ptype='line', **kwargs)
        """
        super(LinePlot, self).__init__(id=id, x=x, y=y, ptype='line', **kwargs)


class ScatterPlot(Plot, PyD3Plus):

    def __init__(self, id, x, y, size=3, **kwargs):
        """Plot a scatter plot.
        This is just syntactic sugar for Plot(id, x, y, ptype='scatter', **kwargs)
        """
        super(ScatterPlot, self).__init__(id=id, x=x,
                                          y=y, ptype='scatter', size=size, **kwargs)


class BoxPlot(Plot):

    def __init__(self, id, x, y, **kwargs):
        """Plot a boxplot.
        This is just syntactic sugar for Plot(id, x, y, ptype='box', **kwargs)
        """
        super(BoxPlot, self).__init__(id=id, x=x, y=y, ptype='box', **kwargs)


class BarPlot(Plot):

    def __init__(self, id, x, y, **kwargs):
        """Plot a barplot.
        This is just syntactic sugar for Plot(id, x, y, ptype='bar', **kwargs)
        """
        super(BarPlot, self).__init__(id=id, x=x, y=y, ptype='bar', **kwargs)


class StackedArea(Plot):

    def __init__(self, id, x, y, **kwargs):
        """Plot a stacked area.
        This is just syntactic sugar for Plot(id, x, y, ptype='stacked', **kwargs)
        """
        super(StackedArea, self).__init__(
            id=id, x=x, y=y, ptype='stacked', **kwargs)


class TreeMap(PyD3Plus):

    def __init__(self, id=['group', 'id'], value="value", size=None, text=None, color=None,
                 legend=False, tooltip=[], depth=0, **kwargs):
        """Plot a treemap
        Args:
            id (str):  D3Plus id parameter, should be unique for each point. Can be a list of key
            size (str/object), D3Plus size parameter, correspond to the key that contains the size for each category
            value (str): parameter for conveniance. key corresponding to each category size share.
            text (str, optional): D3Plus text parameter
            color (str, optional): D3Plus color parameter
            tooltip (str/list, optional): D3Plus tooltip parameter
            depth (int, optional): D3Plus depth parameter
            **kwargs: All remaning D3plus parameters
        """
        super(TreeMap, self).__init__(**kwargs)
        self.id = id
        self.value = value
        self.text = text
        self.color = color

        if size is None and self.value:
            self.size = {'value': self.value, 'threshold': False}
        else:
            self.size = size
        self.tooltip = tooltip
        self.legend = legend
        self.depth = depth or 0

    def _get_legend(self):
        if self.legend is not None:
            return ".legend({})".format(to_js(self.legend))
        return ""

    def _get_color(self):
        if self.color is not None:
            return ".color({})".format(to_js(self.color))
        return ""

    def _get_tooltip(self):
        if self.tooltip:
            return ".tooltip({})".format(to_js(self.tooltip))
        return ""

    def _get_text(self):
        if self.text is not None:
            return ".text({})".format(to_js(self.text))
        return ""

    def generate_js(self, json_data):
        """Generate the javascript code to plot the data

        Args:
            json_data (dataframe, json string, list of dict): input data, will be automatically formatted as json. 

        Returns: the javascript code
        """

        js = """
        (function (){{

            {supjs}

            var viz_data = {viz_data};

            var viz_{viz_name} = d3plus.viz()
                .container({container})
                .data(viz_data)
                .type("tree_map")
                .id({id})
                .size({size})
                {legend}
                {color}
                {text}
                {tooltip}
                .depth({depth})
                .draw();

        }})();
        """.format(
            supjs=Raw(self.js),
            viz_data=json_data,
            viz_name=self.container_id,
            container=to_js("#" + self.container_id),
            id=to_js(self.id),
            size=to_js(self.size),
            legend=self._get_legend(),
            color=self._get_color(),
            text=self._get_text(),
            tooltip=self._get_tooltip(),
            depth=to_js(self.depth)
        )

        return Javascript(lib=self.JS_LIBS, data=js, css=self.css)


class _GeoMap(PyD3Plus):

    def __init__(self, id='country', value="value", text=None, color=None, tooltip=[], coords=None, **kwargs):
        """Plot a Geo Map using D3Plus 1
        This code cannot be displayed in the notebook (return an error about simplify-js, probably due to conflit)
        But, it can be used to generate the js code for the map, in python
        Args:
            id (str): D3Plus id parameter. Key for which our data is unique, should be the country id in topojson
            value (str): key containing the relevant value for each data
            text (str, optional):  key to use for display text
            color (str, optional): key to use for color. Should be the same as 'value'
            tooltip (list/str, optional): keys to place in tooltip
            coords: json file containing the coordinates of each country, default is topojson/countries.json
            **kwargs: All remaning D3plus parameters
        """
        global LAST_ID
        if kwargs.get('container_id'):
            self.container_id = container_id
        else:
            self.container_id = "d3viz_{}".format(LAST_ID)
            LAST_ID += 1
        self.height = kwargs.get('height', 300)
        self.width = kwargs.get('width', 300)
        self.css = ""
        self.js = ""
        self.JS_LIBS = ['//d3plus.org/js/d3.js',
                        '//d3plus.org/js/topojson.js',
                        '//d3plus.org/js/d3plus.js']
        self.id = id
        self.value = value
        self.text = text or self.id
        self.color = color or self.value
        self.tooltip = tooltip or self.value
        self.coords = coords or "http://d3plus.org/topojson/countries.json"

    def draw(self):
        pass

    def generate_js(self, json_data):
        """Generate the javascript code to plot the data

        Args:
            json_data (dataframe, json string, list of dict): input data, will be automatically formatted as json. 

        Returns: the javascript code
        """

        js = """
        (function (){{

            {supjs}

            var viz_data = {viz_data};

            var viz_{viz_name} = d3plus.viz()
                .container({container})
                .data(viz_data)
                .type("geo_map")
                .coords({coords})
                .id({id})
                .text({text})
                .color({color})
                .tooltip({tooltip})
                .draw();

        }})();
        """.format(
            supjs=Raw(self.js),
            viz_data=json_data,
            viz_name=self.container_id,
            container=to_js("#" + self.container_id),
            coords=to_js(self.coords),
            id=to_js(self.id),
            text=to_js(self.text),
            color=to_js(self.color),
            tooltip=to_js(self.tooltip),
        )

        return Javascript(lib=self.JS_LIBS, data=js, css=self.css)


class _GeoMap2(PyD3Plus):

    def __init__(self, id='id', value="value", text=None, tooltip=[], coords=None, title="", scalepos="bottom", **kwargs):
        """Plot a Choropleth Map.
        This part use D3Plus 2 and cannot be dislayed in the notebook. 
        Its main purpose is to automatically generate the HTML block corresponding to the visualization
        that can then be included in an iframe 

        Args:
            id (str): D3Plus id parameter. Key for which our data is unique, should be the country id in topojson
            value (str): key containing the relevant value for each data
            text (str, optional):  key to use for display text
            tooltip (list/str, optional): keys to place in tooltip
            coords: json file containing the coordinates of each country, default is topojson/countries.json
            title (str): title of the Map
            scalepos (str): position of the legend: bottom, right, left or top
            **kwargs: All remaning D3plus parameters
        """
        self.JS_LIBS = ['https://d3plus.org/js/d3plus-geomap.v0.5.full.min.js']
        self.js = ""
        self.css = ""
        self.id = id
        self.value = value
        self.text = text or self.id
        self.tooltip = tooltip or self.value
        if isinstance(self.tooltip, str):
            self.tooltip = [self.tooltip]
        self.coords = coords or "https://d3plus.org/topojson/countries.json"
        self.title = title
        self.scalepos = scalepos

    def _get_label(self):
        if self.text:
            return """
                    .label(function(d) {{
                       return d.{text};
                    }})
                """.format(text=self.text)
        return ""

    def _get_tooltip(self):
        if self.tooltip:
            return """ 
                .tooltipConfig({
                    body: function(d) {
                        var textx = "";
                        for (var k in tooltipkey) {
                            if(k in d){
                                textx += "<p>"+k + ': '+ d[k]+"</p>";                      
                            }
                        }
                        return textx;
                    }
                })"""
        return ""

    def _get_title(self):
        if self.title:
            return ".title({title})".format(to_js(self.title))
        return ""

    def draw(self):
        pass

    def generate_js(self, json_data):
        """Generate the javascript code to plot the data

        Args:
            json_data (dataframe, json string, list of dict): input data, will be automatically formatted as json. 

        Returns: the javascript code
        """

        js = """
        (function (){{

            {supjs}

            var viz_data = {viz_data};
            var tooltipkey = {tooltip};

            var chart_{viz_name} = new d3plus.Geomap()
                    .data(viz_data)
                    .groupBy({id})
                    .colorScale({value})
                    .topojson({coords})
                    {label}
                    {tooltipconfig}
                    {title};

                chart_{viz_name} 
                    .colorScalePosition({scalepos})
                    .render();
    
        }})();
        """.format(
            supjs=Raw(self.js),
            tooltip=to_js(self.tooltip),
            viz_data=json_data,
            viz_name=self.container_id,
            id=to_js(self.id),
            value=to_js(self.value),
            coords=to_js(self.coords),
            label=self._get_label(),
            tooltipconfig=self._get_tooltip(),
            title=self._get_title(),
            scalepos=to_js(self.scalepos),
        )

        return js  # Javascript(lib=self.JS_LIBS, data=js, css=self.css)

    def draw(self, data):
        """Draw a visualization in the ipython notebook."""
        json_data = self.format_data(data)
        HTML(self.dump_html(json_data))

    def dump_html(self, data, container_id=None):
        """Dump a single-file self-contained html string designed to be loaded
        up into the browser on its own or embedded in a page."""
        json_data = self.format_data(data)

        html_template = """

        <!doctype html>
            <html>
            <head>
                <meta charset="utf-8">
                {scripts}

                <style>
                body {{
                  margin: 0;
                  overflow: hidden;
                }}
                {css}
                </style>

            </head>

            <body></body>
  
            <script>
                {code}
            </script>
        </html>

        """
        script_template = "<script src='{src}' type='text/javascript'></script>"
        scripts = "\n\t".join([script_template.format(src=x)
                               for x in self.JS_LIBS])
        code = self.generate_js(json_data)
        if container_id:
            code = code.replace('#{}'.format(
                self.container_id), '#{}'.format(container_id))

        return html_template.format(scripts=scripts, css=self.css, code=code)
