from shiny import *
from htmltools import *

MyComponent = jsx_tag_create("MyComponent")
print(MyComponent())

ui = TagList(
    tags.script(
        html(
            "function MyComponent(props) { return React.createElement('h4', props, 'Hello World') }"
        )
    ),
    MyComponent(style={"color": "red"}),
)

ui.render()
ui.show()


tabs = navs_tab_card(
    nav("a", "tab a"),
    nav("b", "tab b"),
    nav_spacer(),
    nav_menu("menu", nav("c", "tab c"), align="right"),
)

print(tabs)
tabs.show()
