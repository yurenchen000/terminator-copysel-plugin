
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

import terminatorlib.plugin as plugin
from terminatorlib.translation import _

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
        window = Gtk.Window(title="Copy Sel Text")
        window.set_default_size(600, 400)
        window.set_border_width(10)
        
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
        self.pattern_entry.set_tooltip_text("Regular expression to match PS1 prompts")
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
        self.replace_entry.set_tooltip_text("Text to replace PS1 prompts with")
        #replace_hbox.pack_start(self.replace_entry, True, True, 0)
        pattern_hbox.pack_start(self.replace_entry, True, True, 0)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(button_box, False, False, 0)
        
        #process_button = Gtk.Button(label="Process Text")
        process_button = Gtk.Button(label="Replace")
        process_button.connect("clicked", self.on_process_clicked)
        button_box.pack_start(process_button, True, True, 0)
        
        #original_button = Gtk.Button(label="Show Original")
        original_button = Gtk.Button(label="Original")
        original_button.connect("clicked", self.on_original_clicked)
        button_box.pack_start(original_button, True, True, 0)
        
        #copy_button = Gtk.Button(label="Copy to Clipboard")
        copy_button = Gtk.Button(label="Copy")
        copy_button.connect("clicked", self.on_copy_clicked)
        button_box.pack_start(copy_button, True, True, 0)
        
        # Text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        self.text_view = Gtk.TextView()
        # self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)  # 禁用换行
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.set_text(text)
        scrolled_window.add(self.text_view)
        self.apply_vte_font_to_textview(self.terminal, self.text_view)
        
        window.show_all()
        
        # Store the original text
        self.original_text = text
        self.current_text = text
        self.window = window

        self.on_process_clicked(None)

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
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Text copied to clipboard"
        )
        dialog.run()
        dialog.destroy()

