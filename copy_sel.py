
'''
Terminator Plugin to 
  process selected terminal text

 Author: yurenchen@yeah.net
License: GPLv2
   Site: https://github.com/yurenchen000/terminator-copysel-plugin
'''

import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import Pango
from gi.repository import GLib
from gi.repository import GtkSource

import terminatorlib.plugin as plugin
from terminatorlib.translation import _

from test_sv_lang5A import ConsoleHighlighter

# Every plugin you want Terminator to load *must* be listed in 'AVAILABLE'
#AVAILABLE = ['ProcessSelectedText']
AVAILABLE = ['CopySel']

#class ProcessSelectedText(plugin.MenuItem):
class CopySel(plugin.MenuItem):
    """Add custom commands to the terminal menu"""
    capabilities = ['terminal_menu']

    def __init__(self):
        plugin.MenuItem.__init__(self)
        self.default_ps1_pattern = r'(\[\w+@\w+[ \w]*\][\$#] )'
        # 改进后的PS1 pattern
        self.default_ps1_pattern = r'^([^$#]*?[$#]\s?)'
        self.default_ps1_pattern = r'^[^\$\n]+?\$ '
        self.default_ps1_pattern = r'^([^\$\n]+?\$ )'
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.terminal = None
        self.window = None

    def callback(self, menuitems, menu, terminal):
        """Add our menu items to the menu"""
        #item = Gtk.MenuItem(_('Process Selected Text'))
        #item = Gtk.MenuItem(_(' > Copy Sel'))
        item = Gtk.MenuItem(_(' >  Copy   Sel'))
        item.connect("activate", self.process_selected, terminal)
        menuitems.append(item)


    ### not found https://lazka.github.io/pgi-docs/Vte-2.91/classes/Terminal.html
    # get_text_selected
    # get_text_selected_full
    def get_selected_text1(self, terminal):
        """直接获取 VTE 终端中选中的文本"""
        # 获取选中的文本范围
        (start_col, start_row), (end_col, end_row) = terminal.vte.get_selection()
        
        # 获取选中范围内的文本
        selected_text = terminal.vte.get_text_range(
            start_row, start_col,
            end_row, end_col,
            lambda *args: None  # 不需要额外的过滤函数
        )
        
        return selected_text

    def get_selected_text2(self):
        """通过 PRIMARY 剪贴板获取当前选中的文本（不干扰用户的标准剪贴板）"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)  # 不是 CLIPBOARD
        return clipboard.wait_for_text()  # 获取选中文本

    def process_selected(self, _widget, terminal):
        """Process the selected text in a new window"""
        # Get selected text
        #terminal.vte.copy_clipboard()
        # selected_text = self.clipboard.wait_for_text()
        # selected_text = terminal.vte.get_text_selected(terminal.vte.TEXT)
        # selected_text = self.get_selected_text(terminal)
        selected_text = self.get_selected_text2()
        print('=== sel:', selected_text)
        self.terminal = terminal
        
        if not selected_text:
            dialog = Gtk.MessageDialog(
                transient_for=None,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No text selected"
            )
            dialog.format_secondary_text("Please select some text first.")
            dialog.run()
            dialog.destroy()
            return
        
        # Create processing window
        self.create_processing_window(selected_text)


    def set_win_size(self, terminal):
        # 获取终端窗口的尺寸
        alloc = terminal.get_allocation()
        term_width = alloc.width
        term_height = alloc.height
        print('size:', term_width, term_height)

        # 设置尺寸限制
        max_width = 1000
        max_height = 800
        width = min(term_width, max_width)
        height = min(term_height, max_height)

        self.window.set_default_size(width, height)  # 设置窗口尺寸


    def apply_vte_font_to_textview(self, terminal, textview):
        """将 VTE 终端的字体设置应用到 Gtk.TextView"""
        try:
            vte_font = terminal.vte.get_font()
            if vte_font:
                textview.override_font(vte_font.copy())
                return
        except:
            pass
        
        # 回退到等宽字体
        font_desc = Pango.FontDescription()
        font_desc.set_family("Monospace")
        font_desc.set_size(10 * Pango.SCALE)  # 10pt
        textview.override_font(font_desc)

    def create_processing_window(self, text):
        """Create a window with text processing options"""
        #window = Gtk.Window(title="Process Terminal Text")
        window = Gtk.Window(title="Copy Selected Text")
        window.set_default_size(600, 400)
        window.set_border_width(10)
        window.connect("delete-event", lambda w, e: w.destroy())  # 关闭时触发: 直接销毁
        # window.connect("delete-event", lambda w, e: print('==copy win close'))  # 关闭时触发
        self.window = window
        
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        window.add(vbox)
        
        # Pattern input
        pattern_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(pattern_hbox, False, False, 0)
        
        pattern_label = Gtk.Label(label="PS1 Pattern:")
        #pattern_hbox.pack_start(pattern_label, False, False, 0)
        
        self.pattern_entry = Gtk.Entry()
        self.pattern_entry.set_text(self.default_ps1_pattern)
        self.pattern_entry.set_tooltip_text("RegEx to match PS1")
        pattern_hbox.pack_start(self.pattern_entry, True, True, 0)
        
        # Replacement input
        replace_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(replace_hbox, False, False, 0)
        
        replace_label = Gtk.Label(label="Replacement:")
        #replace_hbox.pack_start(replace_label, False, False, 0)
        #pattern_hbox.pack_start(replace_label, False, False, 0)
        
        self.replace_entry = Gtk.Entry()
        self.replace_entry.set_text("> ")
        self.replace_entry.set_text("$ ")
        self.replace_entry.set_tooltip_text("Text to replace with")
        #replace_hbox.pack_start(self.replace_entry, True, True, 0)
        pattern_hbox.pack_start(self.replace_entry, True, True, 0)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(button_box, False, False, 0)
        
        #process_button = Gtk.Button(label="Process Text")
        process_button = Gtk.Button(label="Replace")
        process_button.connect("clicked", self.on_process_clicked)
        # button_box.pack_start(process_button, True, True, 0)
        button_box.pack_start(process_button, False, False, 0)
        
        #original_button = Gtk.Button(label="Show Original")
        original_button = Gtk.Button(label="Original")
        original_button.connect("clicked", self.on_original_clicked)
        # button_box.pack_start(original_button, True, True, 0)
        button_box.pack_start(original_button, False, False, 0)
        
        #copy_button = Gtk.Button(label="Copy to Clipboard")
        # copy_button = Gtk.Button(label="Copy")
        copy_button = Gtk.Button(label="   Copy   ")
        copy_button.connect("clicked", self.on_copy_clicked)
        # button_box.pack_start(copy_button, True, True, 0)
        button_box.pack_start(copy_button, False, False, 0)
        self.copy_button = copy_button
        
        # Text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        ### A. textview
        # self.text_view = Gtk.TextView()
        ### B. sourceview
        self.source_view = GtkSource.View()
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_auto_indent(True)
        self.source_view.set_highlight_current_line(True)
        self.text_view = self.source_view
        self.source_buffer = self.source_view.get_buffer()

        # self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)  # 禁用换行
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.set_text(text)
        scrolled_window.add(self.text_view)
        self.apply_vte_font_to_textview(self.terminal, self.text_view)
        self.set_win_size(self.terminal)
        

        ## highlighter
        self.highlighter = ConsoleHighlighter(self.text_buffer)
        ## scheme
        self.style_manager = GtkSource.StyleSchemeManager()
        self.add_scheme_combobox(button_box)

        # scheme_id = 'classic'
        scheme_id = 'oblivion'
        scheme = self.style_manager.get_scheme(scheme_id)
        self.source_buffer.set_style_scheme(scheme)



        copy_button.grab_focus()
        copy_button.set_receives_default(True)
        # copy_button.set_can_focus(False)
        copy_button.set_can_default(True)
        copy_button.set_can_focus(True)
        window.set_default(copy_button)
        copy_button.grab_focus()
        copy_button.set_state_flags(Gtk.StateFlags.FOCUSED, True)
        copy_button.queue_draw()

        # def on_window_show(win):
        #     copy_button.grab_focus()

        # window.connect("show", on_window_show)

        window.show_all()
        window.present()
        # GLib.timeout_add(500, lambda: copy_button.grab_focus())
        GLib.timeout_add(500, lambda x: copy_button.grab_focus(),copy_button.queue_draw())
        
        # Store the original text
        self.original_text = text
        self.current_text = text
        self.window = window
        self.on_process_clicked(None)


    def add_scheme_combobox(self, tool_hbox):
        # 创建配色方案选择组合框
        scheme_store = Gtk.ListStore(str, str)  # 第一列是显示名称，第二列是方案ID
        schemes = self.style_manager.get_scheme_ids()
        
        # 添加所有配色方案
        for scheme_id in schemes:
            scheme = self.style_manager.get_scheme(scheme_id)
            scheme_store.append([scheme.get_name(), scheme_id])
        
        scheme_combo = Gtk.ComboBox.new_with_model(scheme_store)
        renderer = Gtk.CellRendererText()
        scheme_combo.pack_start(renderer, True)
        scheme_combo.add_attribute(renderer, "text", 0)
        scheme_combo.set_active(0)
        scheme_combo.connect("changed", self.on_scheme_changed)
        
        # 添加到工具栏
        # scheme_label = Gtk.Label(label="配色")
        # scheme_label = Gtk.Label(label="配色")
        # scheme_label = Gtk.Label(label="")
        scheme_label = Gtk.Box(hexpand=True)

        # tool_hbox.pack_start(scheme_label, False, False, 0)
        tool_hbox.pack_start(scheme_label, True, False, 0)
        # tool_hbox.pack_start(scheme_label, True, True, 0)

        # tool_hbox.pack_start(Gtk.Label(label="配色:"), False, False, 0)
        tool_hbox.pack_start(scheme_combo, False, False, 0)
        # tool_hbox.pack_start(scheme_combo, False, False, 10)
        # tool_hbox.pack_start(scheme_combo, True, False, 10)
        # tool_hbox.pack_start(scheme_combo, False, True, 10)
        # tool_hbox.pack_start(scheme_combo, True, True, 10)
        # tool_hbox.pack_end(Gtk.Label(label="配色:"), False, False, 0)
        # tool_hbox.pack_end(scheme_combo, False, False, 0)

        # tool_hbox.reorder_child(scheme_label, 0)
        # tool_hbox.reorder_child(scheme_combo, 1)

        tool_hbox.reorder_child(scheme_combo, 0)
        tool_hbox.reorder_child(scheme_label, 1)

    def on_scheme_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            scheme_id = model[tree_iter][1]
            scheme = self.style_manager.get_scheme(scheme_id)
            print('---scheme change:', scheme_id, scheme)
            self.source_buffer.set_style_scheme(scheme)

    def on_process_clicked(self, button):
        """Process the text with the given pattern and replacement"""
        pattern = self.pattern_entry.get_text()
        replacement = self.replace_entry.get_text()
        
        print('--pattern:', pattern)
        try:
            #processed_text = re.sub(pattern, replacement, self.original_text)
            processed_text = re.sub(pattern, replacement, self.original_text, flags=re.MULTILINE)

            #processed_text = '===: '+pattern + '\n' + processed_text
            self.text_buffer.set_text(processed_text)
            self.current_text = processed_text
        except re.error as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Invalid regular expression"
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()

    def on_original_clicked(self, button):
        """Show the original text"""
        self.text_buffer.set_text(self.original_text)
        self.current_text = self.original_text

    def on_copy_clicked(self, button):
        """Copy the current text to clipboard"""
        self.clipboard.set_text(self.current_text, -1)
        
        self.copy_button.set_tooltip_text('copied!')
        # 2秒后自动隐藏Tooltip
        GLib.timeout_add(2000, lambda : self.copy_button.set_tooltip_text(''))
        return

        # 显示Tooltip提示
        tooltip = Gtk.Tooltip()
        tooltip.set_text("已复制到剪贴板")
        # tooltip.show()

        # 2秒后自动隐藏Tooltip
        GLib.timeout_add(2000, tooltip.hide)
        return

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Text copied to clipboard"
        )
        dialog.run()
        dialog.destroy()

