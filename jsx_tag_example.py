from htmltools import *
MyComponent = jsx_tag("MyComponent")
print(MyComponent())

ui = tag_list(
  tags.script(html(
    "function MyComponent(props) { return React.createElement('h4', props, 'Hello World') }"
  )),
  MyComponent(style = {"color": "red"})
)

ui.show()

ui.get_dependencies()