import flet as ft
import socket
import random
from datetime import datetime
import json
import os

# Variables globales
AVATARS_COLORS = {}
CONNECTED_USERS = {}  # Diccionario para usuarios conectados
MENTION_MODE = False  # Bandera para controlar el modo mención

# --- Paleta de Colores Actualizada ---
WHATSAPP_PRIMARY = "#008069"      # Color de la barra superior
WHATSAPP_BG = "#0C1317"           # Fondo principal
WHATSAPP_CHAT_BG = "#242626"      # Burbujas de otros
WHATSAPP_MY_MSG_BG = "#005C4B"    # Burbujas propias
WHATSAPP_INPUT_BG = "#1F2C34"     # Área de entrada
WHATSAPP_TEXT_COLOR = "#E9EDEF"   # Texto principal
WHATSAPP_SYSTEM_MSG = "#8696A0"   # Mensajes del sistema
WHATSAPP_TIME_COLOR = "#667781"   # Color de la hora
WHATSAPP_CHECKMARK = "#53BDEB"    # Checkmarks azules
WHATSAPP_REPLY_BAR = "#1F2C34"    # Barra de respuesta
WHATSAPP_ICON_COLOR = "#AEBAC1"   # Color de iconos

# --- EMOJI DATASET: Gemoji ---
EMOJI_LIST = []
EMOJI_CATEGORIES = {}
emoji_json_path = os.path.join(os.path.dirname(__file__), "emoji.json")
with open(emoji_json_path, "r", encoding="utf-8") as f:
    EMOJI_LIST = json.load(f)

# Agrupar emojis por categoría para tabs
for emoji in EMOJI_LIST:
    category = emoji.get("category", "Other")
    if not category:
        category = "Other"
    if category not in EMOJI_CATEGORIES:
        EMOJI_CATEGORIES[category] = []
    if emoji.get("emoji"):
        EMOJI_CATEGORIES[category].append(emoji)

# Funciones de utilidad
def get_avatar(name):
    """Función para obtener los avatares"""
    return name.strip()[0].upper() if name and name.strip() else "?"

def set_avatar_colors(nombre):
    """Función para establecer los colores de los avatares"""
    if nombre not in AVATARS_COLORS:
        tonalidades = {
            "PURPLE": ("PURPLE_900", "PURPLE_300"),
            "YELLOW": ("YELLOW_900", "YELLOW_300"),
            "INDIGO": ("INDIGO_900", "INDIGO_300"),
            "BLUE": ("BLUE_900", "BLUE_300"),
            "GREY": ("GREY_900", "GREY_300"),
            "TEAL": ("TEAL_900", "TEAL_300"),
            "GREEN": ("GREEN_900", "GREEN_300"),
            "PINK": ("PINK_900", "PINK_300"),
            "CYAN": ("CYAN_900", "CYAN_300"),
            "LIME": ("LIME_900", "LIME_300"),
            "ORANGE": ("ORANGE_900", "ORANGE_300"),
            "BROWN": ("BROWN_900", "BROWN_300"),
            "DEEP_PURPLE": ("DEEP_PURPLE_900", "DEEP_PURPLE_300"),
        }
        tonalidad = random.choice(list(tonalidades.values()))
        AVATARS_COLORS[nombre] = (
            getattr(ft.Colors, tonalidad[0]),
            getattr(ft.Colors, tonalidad[1])
        )
    return AVATARS_COLORS[nombre]

# Componentes UI
def create_user_dropdown():
    """Función para crear la lista de los usuarios conectados para las menciones"""
    return ft.Container(
        content=ft.ListView(spacing=5, padding=5, height=150, width=200),
        visible=False,
        bgcolor="#242626",
        border_radius=10,
        padding=5,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK54, offset=ft.Offset(1, 1))
    )

def create_emoji_picker(message_field):
    """Función para crear el selector de emojis con categorías y búsqueda"""
    # Barra de búsqueda
    search_field = ft.TextField(
        hint_text="Buscar emoji, alias o categoría...",
        border=ft.InputBorder.UNDERLINE,
        border_radius=5,
        border_color="#21C063",
        filled=True,
        bgcolor="#242626",
        content_padding=10,
        text_size=14,
        on_change=lambda e: filter_emojis_gemoji(e, emoji_picker_container, message_field),
    )

    # Contenedor principal que mostraremos/ocultaremos
    emoji_picker_container = ft.Container(
        width=370,
        height=400,
        bgcolor="#242626",
        border_radius=10,
        padding=5,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=ft.Colors.BLACK54,
            offset=ft.Offset(1, 1)),
        visible=False
    )

    # Creamos tabs con contenido real
    tabs = []
    for category in EMOJI_CATEGORIES.keys():
        tabs.append(
            ft.Tab(
                text=category,
                content=create_emoji_grid(category, message_field)
            )
        )

    category_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=tabs
    )

    # Construimos el contenido final
    emoji_picker_container.content = ft.Column(
        controls=[
            ft.Container(
                content=search_field,
                padding=ft.padding.only(left=10, right=10, top=10, bottom=5),
            ),
            category_tabs
        ],
        scroll=ft.ScrollMode.ADAPTIVE
    )

    return emoji_picker_container

def create_sidebar(page, current_user_name, on_logout_click, on_chats_click, on_settings_click, on_profile_click,):
    """Crea la barra lateral estilo WhatsApp Desktop"""
    avatar_bg_color, avatar_text_color = set_avatar_colors(current_user_name)
    # Estado para mostrar/ocultar el panel de chats
    if not hasattr(page, "show_chats_panel"):
        page.show_chats_panel = False  # Por defecto OCULTO

    def toggle_chats_panel(e):
        page.show_chats_panel = not page.show_chats_panel
        # Solo animar el panel de chats, no limpiar toda la UI
        # Buscar el contenedor del panel de chats y actualizar su visibilidad/width
        for c in page.controls:
            if isinstance(c, ft.Container) and c.content and isinstance(c.content, ft.Stack):
                for stack_child in c.content.controls:
                    if isinstance(stack_child, ft.Row):
                        # Sidebar, panel de chats, panel principal
                        if len(stack_child.controls) > 1:
                            chats_panel = stack_child.controls[1]
                            if isinstance(chats_panel, ft.Container):
                                chats_panel.visible = page.show_chats_panel
                                chats_panel.width = 270 if page.show_chats_panel else 0
                                chats_panel.update()
        page.update()

    return ft.Container(
        content=ft.Column(
            controls=[
                # Botón de menú (barritas horizontales)
                ft.IconButton(
                    icon=ft.Icons.MENU,
                    icon_color=WHATSAPP_ICON_COLOR,
                    tooltip="Mostrar/Ocultar chats",
                    on_click=toggle_chats_panel,
                    icon_size=24,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color={"": "transparent", "hovered": "transparent"}
                    )
                ),
                # --- Parte superior (ícono de chats) ---
                ft.IconButton(
                    icon=ft.Icons.CHAT_OUTLINED,
                    icon_color=WHATSAPP_ICON_COLOR,
                    selected_icon=ft.Icons.CHAT,
                    tooltip="Chats",
                    on_click=on_chats_click,
                    icon_size=24,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color={"": "transparent", "hovered": "transparent"}
                    )
                ),

                # --- Espacio flexible ---
                ft.Column(expand=True),

                # --- Parte inferior ---
                # Separador
                ft.Divider(height=1, color=WHATSAPP_INPUT_BG),

                # Ícono de configuración
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    icon_color=WHATSAPP_ICON_COLOR,
                    tooltip="Configuración",
                    on_click=on_settings_click,
                    icon_size=24,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color={"": "transparent", "hovered": "transparent"}
                    )
                ),

                # Avatar del usuario
                ft.IconButton(
                    content=ft.Container(
                        content=ft.Text(
                            get_avatar(current_user_name),
                            color=avatar_text_color,
                            size=14,
                            weight=ft.FontWeight.BOLD
                        ),
                        alignment=ft.alignment.center,
                        bgcolor=avatar_bg_color,
                        width=32,
                        height=32,
                        border_radius=16
                    ),
                    style=ft.ButtonStyle(
                        color=WHATSAPP_ICON_COLOR,
                        shape=ft.CircleBorder(),
                        overlay_color={"": "transparent", "hovered": "transparent"}
                    ),
                    tooltip=f"Tu perfil: {current_user_name}",
                    on_click=on_profile_click,
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        width=60,
        bgcolor="#161717",
        padding=ft.padding.symmetric(vertical=10),
        border=ft.border.only(right=ft.border.BorderSide(1, WHATSAPP_CHAT_BG))
    )

def create_chat_panel(messages, user_dropdown, emoji_picker):
    """Función para crear la sala donde se muestran los mensajes"""
    return ft.Stack(
        controls=[
            ft.Row(expand=True, controls=[
                ft.Image(src="/chatbg.svg", fit=ft.ImageFit.FILL, opacity=0.2, expand=True),
                ft.Image(src="/chatbg.svg", fit=ft.ImageFit.FILL, opacity=0.2, expand=True)
            ]),
            messages,
            ft.Container(content=user_dropdown, alignment=ft.alignment.bottom_left, bottom=0, left=20, animate_position=100),
            ft.Container(content=emoji_picker, alignment=ft.alignment.bottom_right, bottom=0, left=20, animate_position=100)
        ],
        expand=True
    )

def create_input_panel(message, send_click, on_message_change, toggle_emoji_picker):
    """Función para crear el boton de los emojis, la entrada del mensaje y el boton de enviar"""
    # Ajuste: El TextField ahora usa un Container para controlar mejor el alto y padding,
    # y se ajustan min_lines/max_lines y el tamaño de fuente para evitar recortes.
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.EMOJI_EMOTIONS_OUTLINED,
                    icon_color=WHATSAPP_ICON_COLOR,
                    on_click=toggle_emoji_picker,
                    tooltip="Emojis",
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        overlay_color={"": "transparent", "hovered": "transparent"}
                    )
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(left=0, right=0),
                    content=ft.TextField(
                        ref=message,
                        hint_text="Escribe un mensaje...",
                        min_lines=2,
                        max_lines=6,
                        expand=True,
                        border_color="#161717",
                        focused_border_color="#161717",
                        on_submit=send_click,
                        on_change=on_message_change,
                        filled=True,
                        bgcolor="#242626",
                        border_radius=25,
                        shift_enter=True,
                        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=16, height=1.25),
                        content_padding=ft.padding.only(left=18, right=18, top=12, bottom=12),
                        cursor_color="#21C063",
                        cursor_width=2,
                        cursor_height=22,
                        autofocus=False,
                        multiline=True,
                        # El alto se ajusta automáticamente por min_lines/max_lines
                    )
                ),
                ft.IconButton(
                    icon=ft.Icons.SEND_OUTLINED,
                    icon_color="#161717",
                    bgcolor="#21C063",
                    on_click=send_click,
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=10,
        height=None,  # Permitir que el alto crezca según el contenido
        alignment=ft.alignment.center_left,
    )

def insert_emoji(e, emoji_char, message_field):
    """Inserta un emoji en el campo de mensaje en la posición actual del cursor"""
    if message_field.current:
        current_text = message_field.current.value or ""
        # Insertar el emoji al final del texto (no se puede manipular el cursor)
        new_text = current_text + emoji_char
        message_field.current.value = new_text
        message_field.current.focus()
        message_field.current.update()

def toggle_emoji_picker(e, emoji_picker, user_dropdown):
    """Alterna la visibilidad del selector de emojis"""
    emoji_picker.visible = not emoji_picker.visible
    # Ocultar el dropdown de usuarios si el selector de emojis está visible
    if emoji_picker.visible:
        user_dropdown.visible = False
    emoji_picker.update()
    user_dropdown.update()

def filter_emojis_gemoji(e, emoji_picker, message_field):
    """Filtra emojis por descripción, alias o categoría usando gemoji"""
    search_text = e.control.value.lower()
    filtered_by_category = {}
    for category, emojis in EMOJI_CATEGORIES.items():
        filtered = []
        for emoji_obj in emojis:
            emoji_char = emoji_obj.get("emoji", "")
            description = emoji_obj.get("description", "").lower()
            aliases = [a.lower() for a in emoji_obj.get("aliases", [])]
            tags = [t.lower() for t in emoji_obj.get("tags", [])]
            if (
                search_text in emoji_char
                or search_text in description
                or any(search_text in a for a in aliases)
                or any(search_text in t for t in tags)
                or search_text in category.lower()
            ):
                filtered.append(emoji_obj)
        if filtered:
            filtered_by_category[category] = filtered

    # Creamos un nuevo control Tabs con los resultados filtrados
    new_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text=category,
                content=create_emoji_grid(category, message_field)
            ) for category in filtered_by_category
        ]
    )
    # Reemplazamos el control de tabs en el contenedor
    emoji_picker.content.controls[1] = new_tabs
    emoji_picker.update()

def create_emoji_grid(category_name, message_field):
    """Funcion para crear el grid con los emojis"""
    grid = ft.GridView(
        runs_count=8,
        max_extent=40,
        child_aspect_ratio=1,
        spacing=5,
        run_spacing=5,
        padding=10,
        expand=False,  # Evita que el grid crezca infinitamente
        height=250,    # Altura fija para asegurar scroll limitado
        auto_scroll=False  # Desactiva auto-scroll
    )

    for emoji_obj in EMOJI_CATEGORIES[category_name]:
        emoji_char = emoji_obj.get("emoji", "?")
        description = emoji_obj.get("description", "")
        aliases = emoji_obj.get("aliases", [])
        tooltip = f"{description} ({', '.join(aliases)})" if aliases else description
        grid.controls.append(
            ft.TextButton(
                content=ft.Text(emoji_char, size=20),
                on_click=lambda e, emoji=emoji_char: insert_emoji(e, emoji, message_field),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    padding=5,
                ),
                tooltip=tooltip or f"Insertar {emoji_char}",
            )
        )

    return ft.Container(content=grid, height=250, width=350)

def on_user_hover(e):
    """Función para manejar el hover de los usuarios de la lista de menciones"""
    e.control.opacity = 0.9 if e.data == "true" else 1.0
    e.control.bgcolor = "#3D3F3F" if e.data == "true" else "#2D2F2F"
    e.control.update()

def select_user(selected_user, message, user_dropdown, page, emoji_picker):
    """Función para seleccionar usuario de la lista de menciones"""
    current_text = message.current.value
    if "@" in current_text:
        parts = current_text.rsplit("@", 1)
        message.current.value = f"{parts[0]}@{selected_user} "
    else:
        message.current.value = f"{current_text}@{selected_user} "
    user_dropdown.visible = False
    emoji_picker.visible = False
    message.current.focus()
    page.update()

def show_user_dropdown(page, user, connected_users, user_dropdown, message, emoji_picker):
    """Función para mostrar las lista de usuarios conectados para las menciones"""
    if not user.current or not user.current.value:
        return

    current_user = user.current.value.strip()
    users = [u for u in connected_users.keys() if u != current_user and u.strip()]

    user_dropdown.content.controls = [
        ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=18),
                        width=28, height=28, border_radius=14, bgcolor="#454545",
                        alignment=ft.alignment.center, margin=ft.margin.only(right=8)
                    ),
                    ft.Text(f"~ {u}", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.START, spacing=5
            ),
            on_click=lambda e, u=u: select_user(u, message, user_dropdown, page, emoji_picker),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=8,
            bgcolor="#2D2F2F",
            on_hover=on_user_hover,
            tooltip=f"Mencionar a {u}",
        ) for u in sorted(users)
    ]

    user_dropdown.visible = bool(users)
    # Ocultar el selector de emojis si mostramos el dropdown de usuarios
    if user_dropdown.visible:
        emoji_picker.visible = False

    page.update()

def show_user_info(e):
    """Funcion para mostrar un modal con la información de usuario"""
    # Alternativamente, buscar en variable global CONNECTED_USERS
    global CONNECTED_USERS

    # Obtener referencias globales a los campos de mensaje y usuario
    page = e.page

    # Buscar referencias a los campos de mensaje y usuario
    message_field = None
    user_field = None

    sender_name = e.control.data
    dialog_avatar_bg_color, dialog_avatar_text_color = set_avatar_colors(sender_name)

    # Obtener la referencia al campo de mensaje desde la página
    message_ref = getattr(page, 'message_ref', None)
    if not message_ref or not message_ref.current:
        return

    for c in page.controls:
        if isinstance(c, ft.Column):
            for subc in c.controls:
                if isinstance(subc, ft.Container) and hasattr(subc.content, 'controls'):
                    for rowc in subc.content.controls:
                        if isinstance(rowc, ft.TextField):
                            message_field = rowc
    # Alternativamente, buscar en page.overlay si no se encuentra
    if not message_field:
        for o in page.overlay:
            if isinstance(o, ft.TextField):
                message_field = o

    # Obtener la IP real del usuario si está disponible en CONNECTED_USERS
    user_ip = "0.0.0.0"
    if hasattr(page, 'CONNECTED_USERS'):
        user_dict = getattr(page, 'CONNECTED_USERS')
        if isinstance(user_dict, dict):
            user_info = user_dict.get(sender_name)
            if isinstance(user_info, dict) and 'ip' in user_info:
                user_ip = user_info['ip']

    if sender_name in CONNECTED_USERS:
        user_info = CONNECTED_USERS[sender_name]
        if isinstance(user_info, dict) and 'ip' in user_info:
            user_ip = user_info['ip']

    def mention_user_in_message_field(ev):
        if message_ref and message_ref.current:
            current_text = message_ref.current.value or ""
            if "@" in current_text:
                parts = current_text.rsplit("@", 1)
                message_ref.current.value = f"{parts[0]}@{sender_name} "
            else:
                message_ref.current.value = f"{current_text}@{sender_name} "
            message_ref.current.focus()
            message_ref.current.update()
        dialog.open = False
        page.update()

    # Crear avatar circular para el dialogo
    avatar_item = ft.Container(
        content=ft.Text(
            get_avatar(sender_name),
            color=dialog_avatar_text_color,
            size=40,
            weight=ft.FontWeight.BOLD
        ),
        alignment=ft.alignment.center,
        bgcolor=dialog_avatar_bg_color,
        width=85,
        height=85,
        border_radius=50,
        border=ft.border.all(width=4, color="#242626"),
    )

    content_dialog = ft.Container(
        content=ft.Column(
            controls=[
                avatar_item,
                ft.Text(f"~ {sender_name}", size=18, text_align=ft.TextAlign.CENTER),
                ft.Text(user_ip, size=12, text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY),
                ft.Divider()
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=150,
        height=170,
        padding=10
    )

    dialog = ft.AlertDialog(
        content=content_dialog,
        actions=[
            ft.OutlinedButton(
                text="@mencionar",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    side=ft.BorderSide(color="#21c063", width=1),
                    color="#21c063"
                ),
                on_click=mention_user_in_message_field
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )

    if dialog not in page.overlay:
        page.overlay.append(dialog)

    page.dialog = dialog
    dialog.open = True
    page.update()

def on_message_change(e, page, user, connected_users, user_dropdown, message, emoji_picker):
    """Función para detectar cuando se escribe el caracter @ para las menciones"""
    global MENTION_MODE
    text = e.control.value
    if "@" in text:
        last_at_pos = text.rfind("@")
        if last_at_pos == len(text)-1 or " " not in text[last_at_pos:]:
            MENTION_MODE = True
            show_user_dropdown(page, user, connected_users, user_dropdown, message, emoji_picker)
            return
    MENTION_MODE = False
    user_dropdown.visible = False
    page.update()

def send_click(e, page, user, message, emoji_picker, user_dropdown):
    """Función para enviar el mensaje"""
    if user.current.value and message.current.value:
        page.pubsub.send_all(f"{user.current.value}: {message.current.value}")
        message.current.value = ""
        # Ocultar selectores al enviar
        emoji_picker.visible = False
        user_dropdown.visible = False
        page.update()
    else:
        page.snack_bar = ft.SnackBar(ft.Text("Por favor ingresa un mensaje"))
        page.snack_bar.open = True
        page.update()

def on_message(page, messages, user, msg, user_dropdown, emoji_picker):
    """Función para manejar los mensajes del sistema y los mensjes de los usuarios"""
    if not user.current or not user.current.value:
        return

    is_my_message = msg.startswith(f"{user.current.value}:")
    is_system_message = msg.startswith("[Sistema]")

    if is_system_message:
        if "se conectó" in msg:
            # Extraer nombre y posible IP
            partes = msg.split("[Sistema] ")[1].split(" se conectó")
            new_user = partes[0]
            ip = None
            if "desde" in partes[-1]:
                try:
                    ip = partes[-1].split("desde")[-1].strip()
                except ImportError:
                    ip = None
            if ip:
                CONNECTED_USERS[new_user] = {"ip": ip}
            else:
                CONNECTED_USERS[new_user] = {"ip": "0.0.0.0"}
            if MENTION_MODE and user_dropdown.visible:
                show_user_dropdown(page, user, CONNECTED_USERS, user_dropdown, messages, emoji_picker)

        elif "se desconectó" in msg:
            disconnected_user = msg.split("[Sistema] ")[1].split(" se desconectó")[0]
            CONNECTED_USERS.pop(disconnected_user, None)
            if user_dropdown.visible:
                show_user_dropdown(page, user, CONNECTED_USERS, user_dropdown, messages, emoji_picker)

        # Mostrar mensaje del sistema
        messages.controls.append(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            msg,
                            size=12,
                            italic=True,
                            color="#888888"
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=ft.Colors.BLACK12,
                        border_radius=6
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.update()
        return

    # Procesar mensajes normales
    sender_name = msg.split(": ")[0] if ": " in msg else "Anónimo"
    msg_text = msg.split(": ")[1] if ": " in msg else msg

    # Procesar menciones en el texto
    message_spans = []
    for part in msg_text.split():
        if part.startswith("@"):
            mentioned_user = part[1:]
            if mentioned_user in CONNECTED_USERS or mentioned_user == user.current.value.strip():
                message_spans.append(
                    ft.TextSpan(
                        part + " ",
                        style=ft.TextStyle(color="#21C063", weight=ft.FontWeight.BOLD),
                        data=mentioned_user,
                        on_click=show_user_info
                    )
                )
                continue
        message_spans.append(ft.TextSpan(part + " "))

    # Configurar colores del avatar
    avatar_bg_color, avatar_text_color = set_avatar_colors(sender_name)

    # Crear avatar
    avatar = ft.Container(
        content=ft.Text(
            get_avatar(sender_name),
            color=avatar_text_color,
            size=14,
            weight=ft.FontWeight.BOLD
        ),
        alignment=ft.alignment.center,
        bgcolor=avatar_bg_color,
        width=32,
        height=32,
        border_radius=16,
        margin=ft.margin.only(right=10) if is_my_message else ft.margin.only(left=10),
        tooltip=sender_name,
        data=sender_name,
        on_click=show_user_info
    )

    # Burbuja de chat con ancho máximo y wrap real, sin separar el avatar
    chat_bubble = ft.Container(
        content=ft.Column([
            ft.Text(
                spans=message_spans,
                color=WHATSAPP_TEXT_COLOR,
                selectable=True,
                no_wrap=False,
                max_lines=None,
            ),
            ft.Row([
                ft.Text(
                    datetime.now().strftime("%H:%M"),
                    size=10,
                    color=WHATSAPP_TIME_COLOR
                ),
                ft.Icon(
                    name=ft.Icons.DONE_ALL,
                    size=14,
                    color=WHATSAPP_CHECKMARK
                ) if is_my_message else ft.Container(width=0)
            ], alignment=ft.MainAxisAlignment.END)
        ]),
        bgcolor=WHATSAPP_MY_MSG_BG if is_my_message else WHATSAPP_CHAT_BG,
        border_radius=ft.border_radius.only(
            top_left=8 if is_my_message else 0,
            top_right=0 if is_my_message else 8,
            bottom_left=8,
            bottom_right=8
        ),
        margin=ft.margin.only(
            left=8 if is_my_message else 0,
            right=0 if is_my_message else 8
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        shadow=ft.BoxShadow(
            spread_radius=0.5,
            blur_radius=2,
            color=ft.Colors.BLACK12
        ),
        alignment=ft.alignment.top_left,
        expand=False,
        width=350,
    )

    # Organizar elementos (avatar y burbuja) según quien envía el mensaje
    row_content = [chat_bubble, avatar] if is_my_message else [avatar, chat_bubble]

    # Añadir mensaje al chat
    messages.controls.append(
        ft.Row(
            row_content,
            alignment=ft.MainAxisAlignment.END if is_my_message else ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=10
        )
    )
    page.update()

# Funciones de manejo de eventos
def handle_disconnect(page, user, connected_users):
    """Función para manejar el evento si se cierra la ventana"""
    if user.current and user.current.value:
        username = user.current.value.strip()
        page.pubsub.send_others(f"[Sistema] {username} se desconectó")
        connected_users.pop(username, None)
    page.update()

def logout(e, page, user, connected_users, messages):
    """Función para manejar el evento de cerrar sesión"""
    if user.current and user.current.value:
        username = user.current.value.strip()
        page.pubsub.send_all(f"[Sistema] {username} se desconectó")
        connected_users.pop(username, None)

    page.clean()
    messages.controls.clear()
    user.current.value = ""
    # Asignar el overlay al dialogo del login
    page.dialog = page.overlay[0]
    # Abrir el diálogo de bienvenida
    page.dialog.open = True
    page.update()

# Función principal
def main(page: ft.Page):
    """Función principal pa manejar el diseño de la aplicacion"""
    page.title = "Chat Flet"
    page.bgcolor = "#1D1F1F"
    page.window.title_bar_hidden = True
    page.window.center()
    page.padding = 0

    # Referencias
    user = ft.Ref[ft.TextField]()
    message = ft.Ref[ft.TextField]()

    page.message_ref = message

    # Componentes UI
    user_dropdown = create_user_dropdown()
    emoji_picker = create_emoji_picker(message)
    messages = ft.ListView(auto_scroll=True, expand=True, spacing=10, padding=10)
    chat_panel = create_chat_panel(messages, user_dropdown, emoji_picker)

    # Wrappers para manejar dependencias
    def wrapped_send_click(e):
        send_click(e, page, user, message, emoji_picker, user_dropdown)

    def wrapped_toggle_emoji_picker(e):
        toggle_emoji_picker(e, emoji_picker, user_dropdown)

    def wrapped_on_message_change(e):
        on_message_change(e, page, user, CONNECTED_USERS, user_dropdown, message, emoji_picker)

    def wrapped_logout(e):
        logout(e, page, user, CONNECTED_USERS, messages)

    def wrapped_on_message(msg):
        on_message(page, messages, user, msg, user_dropdown, emoji_picker)

    input_panel = create_input_panel(message, wrapped_send_click, wrapped_on_message_change, wrapped_toggle_emoji_picker)

    # Diálogo de nombre
    name_input = ft.TextField(
        label="Tu nombre",
        width=300,
        border_color="#21C063",
        label_style=ft.TextStyle(color="#21C063"),
        autofocus=True,
        on_submit=lambda e: accept_name(e)
    )

    def accept_name(e):
        """Función para ingresar el nombre de usuario"""
        if not name_input.value.strip():
            page.snack_bar = ft.SnackBar(ft.Text("¡Debes ingresar un nombre!"))
            page.snack_bar.open = True
            page.update()
            return

        page.dialog.open = False
        initialize_ui()
        page.update()

        nombre = name_input.value.strip()
        ip = socket.gethostbyname(socket.gethostname())

        user.current = ft.TextField(value=nombre)
        # Guardar la IP real en el diccionario de usuarios conectados
        CONNECTED_USERS[nombre] = {"ip": ip}

        messages.controls.append(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            f"¡Bienvenido a la sala de chat, {nombre}!",
                            size=12, italic=True, color="#888888"
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=ft.Colors.BLACK12, border_radius=6
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.update()
        page.pubsub.send_others(f"[Sistema] {nombre} se conectó desde {ip}")

    page.dialog = ft.AlertDialog(
        modal=True,
        content=ft.Column(
            [
                ft.Icon(
                    name=ft.Icons.MESSAGE,
                    size=60,
                    color="#21c063"
                ),
                ft.Text(
                    "Bienvenido",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Ingresa tu nombre para comenzar:",
                    size=14,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
                name_input,
                ft.ElevatedButton(
                    text="Entrar",
                    on_click=accept_name,
                    style=ft.ButtonStyle(
                        bgcolor="#21c063",
                        color=ft.Colors.WHITE,
                        padding=10,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True
        ),
        actions_alignment=ft.MainAxisAlignment.CENTER
    )

    def initialize_ui():
        # Permitir que el sidebar pueda llamar a esta función para refrescar la UI
        page._init_ui_func = initialize_ui
        """Función para crear la interfaz"""
        # --- REDISEÑO VISUAL ESTILO WHATSAPP-CLONE ---
        page.add(
            ft.Container(
                expand=True,
                bgcolor="#282828",
                border_radius=12,
                content=ft.Stack(
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=0,
                            controls=[
                                # Sidebar
                                create_sidebar(
                                    page=page,
                                    current_user_name=name_input.value.strip(),
                                    on_logout_click=wrapped_logout,
                                    on_chats_click=lambda e: print("Abrir chats"),
                                    on_settings_click=lambda e: print("Abrir configuración"),
                                    on_profile_click=lambda e: print("Abrir perfil"),
                                ),
                                # Panel de chats (columna izquierda) (ocultable)
                                ft.Container(
                                    width=0 if not getattr(page, "show_chats_panel", False) else 270,
                                    bgcolor="#202020",
                                    visible=getattr(page, "show_chats_panel", False),
                                    animate=ft.Animation(700, ft.AnimationCurve.DECELERATE),
                                    content=ft.Column(
                                        controls=[
                                            ft.Container(
                                                height=40,
                                                padding=ft.padding.only(left=10),
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.MESSAGE, color="#efefef"),
                                                        ft.Text("WhatsApp", size=14, color="#efefef")
                                                    ]
                                                )
                                            ),
                                            ft.Container(
                                                content=ft.Row(
                                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                    controls=[
                                                        ft.Text("Chats", size=24, weight=ft.FontWeight.W_500, color="#fff"),
                                                        ft.Row(
                                                            controls=[
                                                                ft.IconButton(icon=ft.Icons.CHAT, icon_color="#efefef", tooltip="Nuevo chat"),
                                                                ft.IconButton(icon=ft.Icons.MORE_VERT, icon_color="#efefef", tooltip="Más opciones"),
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                padding=ft.padding.only(left=20, right=20)
                                            ),
                                            ft.Container(
                                                content=ft.TextField(
                                                    hint_text="Buscar o iniciar chat",
                                                    border=ft.InputBorder.NONE,
                                                    bgcolor="#282828",
                                                    text_style=ft.TextStyle(size=14, color="#6a6a6a"),
                                                    hint_style=ft.TextStyle(size=14, color="#6a6a6a"),
                                                    filled=True,
                                                    height=35,
                                                    content_padding=ft.padding.only(left=15, top=5)
                                                ),
                                                padding=ft.padding.only(left=20, right=20, top=10, bottom=10)
                                            ),
                                            ft.Divider(height=1, color="#363636"),
                                            ft.Container(
                                                expand=True,
                                                content=ft.Column(
                                                    scroll=ft.ScrollMode.AUTO,
                                                    expand=True,
                                                    controls=[
                                                        ft.Container(
                                                            height=70,
                                                            padding=ft.padding.only(left=10, right=10),
                                                            content=ft.Row(
                                                                controls=[
                                                                    ft.Container(
                                                                        height=50,
                                                                        width=50,
                                                                        border_radius=25,
                                                                        bgcolor="#444",
                                                                        content=ft.Icon(ft.Icons.PERSON, color="#fff", size=30)
                                                                    ),
                                                                    ft.Column(
                                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                                        horizontal_alignment=ft.CrossAxisAlignment.START,
                                                                        controls=[
                                                                            ft.Text("WhatsApp", size=16, color="#fff"),
                                                                            ft.Text("último mensaje...", size=12, color="#aaa")
                                                                        ]
                                                                    ),
                                                                    ft.Text("12:20AM", size=12, color="#53BDEB")
                                                                ],
                                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                                            )
                                                        )
                                                    ]
                                                )
                                            )
                                        ],
                                        expand=True,
                                        spacing=0
                                    )
                                ),
                                # Panel principal (chat)
                                ft.Container(
                                    expand=True,
                                    bgcolor="#282828",
                                    content=ft.Column(
                                        controls=[
                                            # Header superior
                                            ft.Container(
                                                padding=ft.padding.only(left=20, right=15),
                                                height=50,
                                                bgcolor="#202020",
                                                content=ft.Row(
                                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    controls=[
                                                        ft.Row(
                                                            controls=[
                                                                ft.Container(
                                                                    height=40,
                                                                    width=40,
                                                                    border_radius=20,
                                                                    bgcolor="#363636",
                                                                    content=ft.Icon(name=ft.Icons.GROUP, color=ft.Colors.GREY_300)
                                                                ),
                                                                ft.Text("Sala Grupal", color=ft.Colors.GREY_300)
                                                            ]
                                                        ),
                                                        ft.Row(
                                                            controls=[
                                                                ft.IconButton(icon=ft.Icons.VIDEO_CALL_OUTLINED, icon_color="#efefef"),
                                                                ft.IconButton(icon=ft.Icons.CALL_OUTLINED, icon_color="#efefef"),
                                                                ft.IconButton(icon=ft.Icons.SEARCH_OUTLINED, icon_color="#efefef"),
                                                                ft.IconButton(icon=ft.Icons.LOGOUT, icon_color="#efefef", tooltip="Cerrar sesión", on_click=wrapped_logout)
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ),
                                            # Fondo y mensajes
                                            ft.Container(
                                                alignment=ft.alignment.top_left,
                                                padding=ft.padding.only(left=20, right=20, top=10),
                                                expand=True,
                                                bgcolor="#1a343434",
                                                content=ft.Stack(
                                                    controls=[
                                                        ft.Image(src="/assets/wallpaper.png", opacity=0.2, fit=ft.ImageFit.COVER, expand=True),
                                                        chat_panel
                                                    ]
                                                )
                                            ),
                                            # Input de mensaje
                                            ft.Container(
                                                margin=ft.margin.only(left=2),
                                                padding=ft.padding.only(left=10, right=10),
                                                height=60,
                                                bgcolor="#202020",
                                                content=input_panel
                                            )
                                        ],
                                        expand=True,
                                        spacing=0
                                    )
                                )
                            ]
                        )
                    ]
                )
            )
        )

    # Configuración final
    page.on_close = lambda _: handle_disconnect(page, user, CONNECTED_USERS)
    page.pubsub.subscribe(wrapped_on_message)
    page.overlay.append(page.dialog)
    page.dialog.open = True
    page.update()

ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="webhosting.cu", port=8080, assets_dir="assets")
