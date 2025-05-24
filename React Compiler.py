import os

def indent(text, spaces=2): #Indent the given text by a specified number of spaces.
    return '\n'.join((' ' * spaces) + line for line in text.splitlines())

def camel_case(prop):
    parts = prop.split('-')
    return parts[0] + ''.join(x.title() for x in parts[1:])

def style_dict(styles):
    if not styles:
        return "{}"
    entries = []
    for s in styles:
        if ':' in s:
            key, value = s.split(':', 1)
            entries.append(f"'{key.strip()}': '{value.strip()}'")
    return '{' + ', '.join(entries) + '}'

def jsx_props (attributes, styles=None, use_inline_styles=False, class_name=None):
    props = []
    for attr, val in attributes.items():
        if attr == "class":
            props.append(f'className="{val}"')
        else:
            props.append(f'{attr}="{val}"')

    if use_inline_styles and styles:
        props.append(f'style={style_dict(styles)}')
    elif styles:
        props.append(f'classname="{class_name}"')
    
    return " " + " ".join(props) if props else ""

def render_component_tree (component, use_inline_styles=False):
    tag = component('type')
    attributes = component.get('attributes', {})
    styles = component.get('styles', {})
    children = component.get('children', [])
    name = component.get('name')

    props = jsx_props(attributes, styles, use_inline_styles, name if not use_inline_styles else None)

    if children:
        inner = "\n".join*([render_component_tree(child, use_inline_styles) for child in children])
        return f'<{tag}{props}>\n{indent(inner, 2)}\n</{tag}>'
    else:
        return f'<{tag}{props} />'
    
def generate_component(component, use_inline_styles, output_dir):
    name = component['name']
    body = render_component_tree(component, use_inline_styles)

    imports = f"import './{name}.css';\n" if not use_inline_styles else ""
    jsx_lines = [
        imports, f"export default function {name}() {{",
        " return (",
        indent(body, 4),
        " );",
        "}"
    ]

    jsx = "\n".join(line for line in jsx_lines if line.strip() != "")

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"{name}.jsx"), 'w') as f:
        f.write(jsx)
    
    if not use_inline_styles:
        css = f".{name} {{\n"
        for style in component.get('styles', []):
           css += f"  {style};\n"
        css += "}"
        with open(os.path.join(output_dir, f"{name}.css"), 'w') as f:
            f.write(css)

def generate_page(page, components_dir, pages_dir, use_inline_styles):
    page_name = page['label']
    imports = []
    elements = []

    for component in page['contents']:
        name = component['name']
        generate_component(component, use_inline_styles, components_dir)
        imports.append(f"import {name} from '../components/{name}';")
        elements.append(f"<{name} />")

    jsx_lines = imports + [
        "",
        f"export default function {page_name}() {{",
        " return (",
        "  <div>",
        indent("\n".join(elements), 6),
        "  </div>",
        " );",
        "}"
    ]

    os.makedirs(pages_dir, exist_ok=True)
    with open(os.path.join(pages_dir, f"{page_name}.jsx"), 'w') as f:
        f.write("\n".join(jsx_lines))

def generate_app(pages, pages_dir):
    imports = [
        "import {",
        "  BrowserRouter as Router,",
        "  Route,",
        "  Routes,",
        "} from 'react-router-dom';",
    ]
    imports += [f"import {page['label']} from './pages/{page['label']}';" for page in pages]

    routes = [f'<Route path="/{page["label"].lower()}" element={{<{page["label"]} />}} />' for page in pages]
    app_jsx = "\n".join(imports) + "\n\n" + \
        "export default function App() {\n" + \
        "  return (\n" + \
        "    <Router>\n" + \
        "      <Routes>\n" + \
        indent ("\n".join(routes), 8) + "\n" + \
        "      </Routes>\n" + \
        "    </Router>\n" + \
        "  );\n" + \
        "}"
    
    with open(os.path.join(pages_dir, "App.jsx"), 'w') as f:
        f.write(app_jsx)

def generate_index_html(output_dir):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React App</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>"""
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html)

def transpilation(json_data, output_root="react_app", use_inline_styles=False):
    components_dir = os.path.join(output_root, "components")
    pages_dir = os.path.join(output_root, "pages")

    pages = json_data.get('pages', [])
    for page in pages:
        generate_page(page, components_dir, pages_dir, use_inline_styles)
    
    generate_app(pages, output_root)
    generate_index_html(output_root)