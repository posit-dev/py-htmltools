
from htmltools import *

x = div(
  h1("Hello htmltools!"),
  id = "foo"
)

# Summary of HTML tag
x

# Print the HTML
print(x)

# Renders the HTML (in IPython or a browser)
x.show()

# If you want attributes first...
x = div(
  id = "foo",
  children = [
    h1("Hello htmltools!"),
    tags.i("for python")
  ]
)

# Or, more consisely...
x = div(id = "foo")(
  h1("Hello htmltools!"),
  tags.i("for python")
)


# Access various attributes and methods
x.name
x.children
x.has_attr("id")
x.get_attr("id")

# Add surrounding '_' to avoid conflict with python keywords
x.append_attrs(_class_  = "bar")
x.append_children(
  tags.p("by RStudio")
)
print(x)

# Save HTML to disk 
x.save_html("index.html")

# view it in a browser
import webbrowser
import os
webbrowser.open('file://' + os.path.realpath("index.html"))


# Create list of tags and pass in HTML dependencies
x = tag_list(
  h1("Hello htmltools!"),
  tags.i("for python"),
  html_dependency(
    name = "bootstrap",
    version = "5.0.1",
    src = "www/shared/bootstrap",
    package = "shiny",
    script = "bootstrap.bundle.min.js",
    stylesheet = "bootstrap.min.css"
 )
)

print(x)
x.get_dependencies()
x.show()



# Some basic Shiny wrappers
from shiny.page import *
from shiny.input import *

ui = fluid(
  h1("Hello Shiny for Python!"),
  action_button("foo", "Hello!")
)

print(ui)
ui.get_dependencies()
ui.show()
