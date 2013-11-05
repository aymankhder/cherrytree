# -*- coding: UTF-8 -*-
#
#       support.py
#
#       Copyright 2009-2013 Giuseppe Penone <giuspen@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import gtk, os
import cons


def text_file_rm_emptylines(filepath):
    """Remove empty lines in a text file"""
    overwrite_needed = False
    fd = open(filepath, 'r')
    file_lines = []
    for file_line in fd:
        if file_line not in ["\r\n", "\n\r", cons.CHAR_NEWLINE]:
            file_lines.append(file_line)
        else: overwrite_needed = True
    fd.close()
    if overwrite_needed:
        print filepath, "empty lines removed"
        fd = open(filepath, 'w')
        fd.writelines(file_lines)
        fd.close()

def clean_from_chars_not_for_filename(filename_in):
    """Clean a string from chars not good for filename"""
    filename_out = filename_in.replace(cons.CHAR_SLASH, cons.CHAR_MINUS).replace(cons.CHAR_BSLASH, cons.CHAR_MINUS)
    filename_out = filename_out.replace(cons.CHAR_STAR, "").replace(cons.CHAR_QUESTION, "").replace(cons.CHAR_COLON, "")
    filename_out = filename_out.replace(cons.CHAR_LESSER, "").replace(cons.CHAR_GREATER, "")
    filename_out = filename_out.replace(cons.CHAR_PIPE, "").replace(cons.CHAR_DQUOTE, "")
    filename_out = filename_out.replace(cons.CHAR_NEWLINE, "").replace(cons.CHAR_CR, "").strip()
    return filename_out.replace(cons.CHAR_SPACE, cons.CHAR_USCORE)

def get_node_hierarchical_name(dad, tree_iter, separator="--"):
    """Get the Node Hierarchical Name"""
    hierarchical_name = dad.treestore[tree_iter][1].strip()
    father_iter = dad.treestore.iter_parent(tree_iter)
    while father_iter:
        hierarchical_name = dad.treestore[father_iter][1].strip() + separator + hierarchical_name
        father_iter = dad.treestore.iter_parent(father_iter)
    hierarchical_name = clean_from_chars_not_for_filename(hierarchical_name)
    if len(hierarchical_name) > cons.MAX_FILE_NAME_LEN:
        hierarchical_name = hierarchical_name[-cons.MAX_FILE_NAME_LEN:]
    return hierarchical_name

def strip_trailing_spaces(text_buffer):
    """Remove trailing spaces/tabs"""
    curr_iter = text_buffer.get_start_iter()
    curr_state = 0
    start_offset = 0
    while curr_iter:
        curr_char = curr_iter.get_char()
        if curr_state == 0:
            if curr_char in [cons.CHAR_SPACE, cons.CHAR_TAB]:
                start_offset = curr_iter.get_offset()
                curr_state = 1
        elif curr_state == 1:
            if curr_char == cons.CHAR_NEWLINE:
                iter_offset = curr_iter.get_offset()
                text_buffer.delete(text_buffer.get_iter_at_offset(start_offset), curr_iter)
                curr_iter = text_buffer.get_iter_at_offset(iter_offset)
                curr_state = 0
            elif not curr_char in [cons.CHAR_SPACE, cons.CHAR_TAB]:
                curr_state = 0
        if not curr_iter.forward_char():
            if curr_state == 1:
                text_buffer.delete(text_buffer.get_iter_at_offset(start_offset), curr_iter)
            break

def get_next_chars_from_iter_are(iter_start, num, chars):
    """Returns True if the Given Chars are the next 'num' after iter"""
    text_iter = iter_start.copy()
    for i in range(num):
        if text_iter.get_char() != chars[i]: return False
        if i != num-1 and not text_iter.forward_char(): return False
    return True

def get_former_line_indentation(iter_start):
    """Returns the indentation of the former paragraph or empty string"""
    if not iter_start.backward_chars(2) or iter_start.get_char() == cons.CHAR_NEWLINE: return ""
    buffer_start = False
    while iter_start:
        if iter_start.get_char() == cons.CHAR_NEWLINE: break # we got the previous paragraph start
        elif not iter_start.backward_char():
            buffer_start = True
            break # we reached the buffer start
    if not buffer_start: iter_start.forward_char()
    if iter_start.get_char() == cons.CHAR_SPACE:
        num_spaces = 1
        while iter_start.forward_char() and iter_start.get_char() == cons.CHAR_SPACE:
            num_spaces += 1
        return num_spaces*cons.CHAR_SPACE
    if iter_start.get_char() == cons.CHAR_TAB:
        num_tabs = 1
        while iter_start.forward_char() and iter_start.get_char() == cons.CHAR_TAB:
            num_tabs += 1
        return num_tabs*cons.CHAR_TAB
    return ""

def windows_cmd_prepare_path(filepath):
    """Prepares a Path to be digested by windows command line"""
    return cons.CHAR_DQUOTE + filepath + cons.CHAR_DQUOTE

def dialog_file_save_as(filename=None, filter_pattern=None, filter_name=None, curr_folder=None, parent=None):
    """The Save file as dialog, Returns the retrieved filepath or None"""
    chooser = gtk.FileChooserDialog(title=_("Save File as"),
                                    action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK) )
    chooser.set_do_overwrite_confirmation(True)
    if parent != None:
        chooser.set_transient_for(parent)
        chooser.set_property("modal", True)
        chooser.set_property("destroy-with-parent", True)
        chooser.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    else: chooser.set_position(gtk.WIN_POS_CENTER)
    if curr_folder == None or os.path.isdir(curr_folder) == False:
        chooser.set_current_folder(os.path.expanduser('~'))
    else:
        chooser.set_current_folder(curr_folder)
    if filename != None:
        chooser.set_current_name(filename)
    if filter_pattern != None:
        filter = gtk.FileFilter()
        filter.set_name(filter_name)
        filter.add_pattern(filter_pattern)
        chooser.add_filter(filter)
    if chooser.run() == gtk.RESPONSE_OK:
        filepath = chooser.get_filename()
        chooser.destroy()
        return unicode(filepath, cons.STR_UTF8, cons.STR_IGNORE) if filepath != None else None
    else:
        chooser.destroy()
        return None

def dialog_file_select(filter_pattern=[], filter_mime=[], filter_name=None, curr_folder=None, parent=None):
    """The Select file dialog, Returns the retrieved filepath or None"""
    chooser = gtk.FileChooserDialog(title = _("Select File"),
                                    action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK) )
    if parent != None:
        chooser.set_transient_for(parent)
        chooser.set_property("modal", True)
        chooser.set_property("destroy-with-parent", True)
        chooser.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    else: chooser.set_position(gtk.WIN_POS_CENTER)
    if curr_folder == None or os.path.isdir(curr_folder) == False:
        chooser.set_current_folder(os.path.expanduser('~'))
    else:
        chooser.set_current_folder(curr_folder)
    if filter_pattern or filter_mime:
        filefilter = gtk.FileFilter()
        filefilter.set_name(filter_name)
        for element in filter_pattern:
            filefilter.add_pattern(element)
        for element in filter_mime:
            filefilter.add_mime_type(element)
        chooser.add_filter(filefilter)
    if chooser.run() == gtk.RESPONSE_OK:
        filepath = chooser.get_filename()
        chooser.destroy()
        return unicode(filepath, cons.STR_UTF8, cons.STR_IGNORE) if filepath != None else None
    else:
        chooser.destroy()
        return None

def dialog_folder_select(curr_folder=None, parent=None):
    """The Select folder dialog, returns the retrieved folderpath or None"""
    chooser = gtk.FileChooserDialog(title = _("Select Folder"),
                                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK) )
    if parent != None:
        chooser.set_transient_for(parent)
        chooser.set_property("modal", True)
        chooser.set_property("destroy-with-parent", True)
        chooser.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    else: chooser.set_position(gtk.WIN_POS_CENTER)
    if curr_folder == None or os.path.isdir(curr_folder) == False:
        chooser.set_current_folder(os.path.expanduser('~'))
    else:
        chooser.set_current_folder(curr_folder)
    if chooser.run() == gtk.RESPONSE_OK:
        folderpath = chooser.get_filename()
        chooser.destroy()
        return unicode(folderpath, cons.STR_UTF8, cons.STR_IGNORE) if folderpath != None else None
    else:
        chooser.destroy()
        return None

def dialog_question(message, parent=None):
    """The Question dialog, returns True if the user presses OK"""
    dialog = gtk.MessageDialog(parent=parent,
                               flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                               type=gtk.MESSAGE_QUESTION,
                               buttons=gtk.BUTTONS_OK_CANCEL,
                               message_format=message)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_title(_("Question"))
    if dialog.run() == gtk.RESPONSE_OK:
        dialog.destroy()
        return True
    else:
        dialog.destroy()
        return False

def dialog_info(message, parent):
    """The Info dialog"""
    dialog = gtk.MessageDialog(parent=parent,
                               flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                               type=gtk.MESSAGE_INFO,
                               buttons=gtk.BUTTONS_OK,
                               message_format=message)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_title(_("Info"))
    dialog.run()
    dialog.destroy()

def dialog_info_after_restart(parent=None):
    """Change Only After Restart"""
    dialog_info(_("This Change will have Effect Only After Restarting CherryTree"), parent)

def dialog_warning(message, parent):
    """The Warning dialog"""
    dialog = gtk.MessageDialog(parent=parent,
                               flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                               type=gtk.MESSAGE_WARNING,
                               buttons=gtk.BUTTONS_OK,
                               message_format=message)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_title(_("Warning"))
    dialog.run()
    dialog.destroy()

def dialog_error(message, parent):
    """The Error dialog"""
    dialog = gtk.MessageDialog(parent=parent,
                               flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                               type=gtk.MESSAGE_ERROR,
                               buttons=gtk.BUTTONS_OK,
                               message_format=message)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_title(_("Error"))
    dialog.run()
    dialog.destroy()

def dialog_about(dad):
    """Application About Dialog"""
    dialog = gtk.AboutDialog()
    dialog.set_program_name("CherryTree")
    dialog.set_version(cons.VERSION)
    dialog.set_copyright(_("""Copyright © 2009-2013
Giuseppe Penone <giuspen@gmail.com>"""))
    dialog.set_comments(_("A Hierarchical Note Taking Application, featuring Rich Text and Syntax Highlighting"))
    dialog.set_license(_("""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.
  
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
  
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""))
    dialog.set_website("http://www.giuspen.com/cherrytree/")
    dialog.set_authors(["Giuseppe Penone <giuspen@gmail.com>"])
    dialog.set_documenters(["Robert Boudreau <RobtTheB@gmail.com>"])
    dialog.set_artists(["OCAL <http://www.openclipart.org/>", "Zeltak <zeltak@gmail.com>", "Angelo Penone <angelo.penone@gmail.com>"])
    dialog.set_translator_credits(_("""Chinese Simplified (zh_CN) Channing Wong <mamimoluo@gmail.com>
Czech (cs) Pavel Fric <fripohled@blogspot.com>
Dutch (nl) Patrick Vijgeboom <pj.vijgeboom@gmail.com>
French (fr) Benoît D'Angelo <benoit.dangelo@gmx.fr> (former Ludovic Troisi)
German (de) Frank Brungräber <calexu@arcor.de> (former Sven Neubauer)
Italian (it) Giuseppe Penone <giuspen@gmail.com>
Polish (pl) Marcin Swierczynski <orneo1212@gmail.com>
Portuguese Brazil (pt_BR) Vinicius Schmidt <viniciussm@rocketmail.com>
Russian (ru) Andriy Kovtun <kovtunos@yandex.ru>
Spanish (es) Daniel MC <i.e.betel@gmail.com>
Ukrainian (uk) Andriy Kovtun <kovtunos@yandex.ru>"""))
    dialog.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(cons.GLADE_PATH, "cherrytree.png")))
    dialog.set_title(_("About CherryTree"))
    dialog.set_transient_for(dad.window)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_modal(True)
    dialog.run()
    dialog.hide()

def dialog_exit_save(father_win):
    """Save before Exit Dialog"""
    dialog = gtk.Dialog(title=_("Warning"),
        parent=father_win,
        flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
        buttons=(_("Cancel"), 6,
                 _("No"), 4,
                 _("Yes"), 2) )
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    try:
        button = dialog.get_widget_for_response(6)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
        button = dialog.get_widget_for_response(4)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
        button = dialog.get_widget_for_response(2)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_BUTTON))
    except: pass
    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
    label = gtk.Label(_("""<b>The current document was updated</b>,
do you want to save the changes?"""))
    label.set_use_markup(True)
    hbox = gtk.HBox()
    hbox.pack_start(image)
    hbox.pack_start(label)
    content_area = dialog.get_content_area()
    content_area.pack_start(hbox)
    def on_key_press_exitdialog(widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == "Return":
            try: dialog.get_widget_for_response(2).clicked()
            except: print cons.STR_PYGTK_222_REQUIRED
        elif keyname == "Escape":
            try: dialog.get_widget_for_response(6).clicked()
            except: print cons.STR_PYGTK_222_REQUIRED
        else: print keyname
        return True
    dialog.connect('key_press_event', on_key_press_exitdialog)
    content_area.show_all()
    response = dialog.run()
    dialog.hide()
    return response

def dialog_selnode_selnodeandsub_alltree(father_win, also_selection, also_node_name=False):
    """Dialog to select between the Selected Node/Selected Node + Subnodes/All Tree"""
    dialog = gtk.Dialog(title=_("Involved Nodes"),
                                parent=father_win,
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    if also_selection: radiobutton_selection = gtk.RadioButton(label=_("Selected Text Only"))
    radiobutton_selnode = gtk.RadioButton(label=_("Selected Node Only"))
    radiobutton_selnodeandsub = gtk.RadioButton(label=_("Selected Node and Subnodes"))
    radiobutton_alltree = gtk.RadioButton(label=_("All the Tree"))
    radiobutton_selnodeandsub.set_group(radiobutton_selnode)
    radiobutton_alltree.set_group(radiobutton_selnode)
    if also_node_name:
        separator_item = gtk.HSeparator()
        checkbutton_node_name = gtk.CheckButton(label=_("Include Node Name"))
        checkbutton_node_name.set_active(True)
    if also_selection: radiobutton_selection.set_group(radiobutton_selnode)
    content_area = dialog.get_content_area()
    if also_selection: content_area.pack_start(radiobutton_selection)
    content_area.pack_start(radiobutton_selnode)
    content_area.pack_start(radiobutton_selnodeandsub)
    content_area.pack_start(radiobutton_alltree)
    if also_node_name:
        content_area.pack_start(separator_item)
        content_area.pack_start(checkbutton_node_name)
    def on_key_press_enter_dialog(widget, event):
        if gtk.gdk.keyval_name(event.keyval) == "Return":
            try: dialog.get_widget_for_response(gtk.RESPONSE_ACCEPT).clicked()
            except: print cons.STR_PYGTK_222_REQUIRED
            return True
    dialog.connect("key_press_event", on_key_press_enter_dialog)
    content_area.show_all()
    response = dialog.run()
    if radiobutton_selnode.get_active(): ret_val = 1
    elif radiobutton_selnodeandsub.get_active(): ret_val = 2
    elif radiobutton_alltree.get_active(): ret_val = 3
    else: ret_val = 4
    if also_node_name and checkbutton_node_name.get_active(): ret_node_name = True
    else: ret_node_name = False
    dialog.destroy()
    if response != gtk.RESPONSE_ACCEPT: ret_val = 0
    return [ret_val, ret_node_name]

def set_bookmarks_menu_items(inst):
    """Set Bookmarks Menu Items"""
    bookmarks_menu = inst.ui.get_widget("/MenuBar/BookmarksMenu").get_submenu()
    for menu_item in inst.bookmarks_menu_items:
        bookmarks_menu.remove(menu_item)
    menu_item = gtk.SeparatorMenuItem()
    menu_item.show()
    bookmarks_menu.append(menu_item)
    inst.bookmarks_menu_items = [menu_item]
    for node_id_str in inst.bookmarks:
        if not long(node_id_str) in inst.nodes_names_dict: continue
        menu_item = gtk.ImageMenuItem(inst.nodes_names_dict[long(node_id_str)])
        menu_item.set_image(gtk.image_new_from_stock("Red Cherry", gtk.ICON_SIZE_MENU))
        menu_item.connect("activate", select_bookmark_node, node_id_str, inst)
        menu_item.show()
        bookmarks_menu.append(menu_item)
        inst.bookmarks_menu_items.append(menu_item)

def set_menu_items_special_chars(inst):
    """Set Special Chars menu items"""
    if not "special_menu_1" in dir(inst):
        inst.special_menu_1 = gtk.Menu()
        first_run = True
    else:
        children_1 = inst.special_menu_1.get_children()
        for children in children_1:
            children.hide()
            del children
        first_run = False
    for special_char in inst.special_chars:
        menu_item = gtk.MenuItem(special_char)
        menu_item.connect("activate", insert_special_char, special_char, inst)
        menu_item.show()
        inst.special_menu_1.append(menu_item)
    if first_run:
        # main menu
        special_menuitem = gtk.ImageMenuItem(_("Insert _Special Character"))
        special_menuitem.set_image(gtk.image_new_from_stock("insert", gtk.ICON_SIZE_MENU))
        special_menuitem.set_tooltip_text(_("Insert a Special Character"))
        special_menuitem.set_submenu(inst.special_menu_1)
        inst.ui.get_widget("/MenuBar/EditMenu").get_submenu().insert(special_menuitem, 14)

def set_menu_items_recent_documents(inst):
    """Set Recent Documents menu items on Menu and Toolbar"""
    if not "recent_menu_1" in dir(inst):
        inst.recent_menu_1 = gtk.Menu()
        inst.recent_menu_2 = gtk.Menu()
        first_run = True
    else:
        children_1 = inst.recent_menu_1.get_children()
        children_2 = inst.recent_menu_2.get_children()
        for children in children_1:
            children.hide()
            del children
        for children in children_2:
            children.hide()
            del children
        first_run = False
    for target in [1, 2]:
        for i, filepath in enumerate(inst.recent_docs):
            if i >= cons.MAX_RECENT_DOCS: break
            menu_item = gtk.ImageMenuItem(filepath)
            menu_item.set_image(gtk.image_new_from_stock("gtk-open", gtk.ICON_SIZE_MENU))
            menu_item.connect("activate", open_recent_document, filepath, inst)
            menu_item.show()
            if target == 1: inst.recent_menu_1.append(menu_item)
            else: inst.recent_menu_2.append(menu_item)
    if first_run:
        # main menu
        recent_menuitem = gtk.ImageMenuItem(_("_Recent Documents"))
        recent_menuitem.set_image(gtk.image_new_from_stock("gtk-open", gtk.ICON_SIZE_MENU))
        recent_menuitem.set_tooltip_text(_("Open a Recent CherryTree Document"))
        recent_menuitem.set_submenu(inst.recent_menu_1)
        inst.ui.get_widget("/MenuBar/FileMenu").get_submenu().insert(recent_menuitem, 9)
        # toolbar
        menu_toolbutton = gtk.MenuToolButton("gtk-open")
        menu_toolbutton.set_tooltip_text(_("Open a CherryTree Document"))
        menu_toolbutton.set_arrow_tooltip_text(_("Open a Recent CherryTree Document"))
        menu_toolbutton.set_menu(inst.recent_menu_2)
        menu_toolbutton.connect("clicked", inst.file_open)
        inst.ui.get_widget("/ToolBar").insert(menu_toolbutton, 9)

def add_recent_document(inst, filepath):
    """Add a Recent Document if Needed"""
    if filepath in inst.recent_docs and inst.recent_docs[0] == filepath:
        return
    if filepath in inst.recent_docs: inst.recent_docs.remove(filepath)
    inst.recent_docs.insert(0, filepath)
    set_menu_items_recent_documents(inst)

def insert_special_char(menu_item, special_char, dad):
    """A Special character insert was Requested"""
    if not dad.is_there_selected_node_or_error(): return
    dad.curr_buffer.insert_at_cursor(special_char)

def open_recent_document(menu_item, filepath, dad):
    """A Recent Document was Requested"""
    if os.path.isfile(filepath): dad.filepath_open(filepath)
    else:
        dialog_error(_("The Document %s was Not Found") % filepath, dad.window)
        menu_item.hide()
        try: dad.recent_docs.remove(filepath)
        except: pass

def select_bookmark_node(menu_item, node_id_str, dad):
    """Select a Node in the Bookmarks List"""
    node_iter = dad.get_tree_iter_from_node_id(long(node_id_str))
    if node_iter: dad.treeview_safe_set_cursor(node_iter)

def bookmarks_handle(dad):
    """Handle the Bookmarks List"""
    dialog = gtk.Dialog(title=_("Handle the Bookmarks List"),
                        parent=dad.window,
                        flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )
    dialog.set_default_size(500, 400)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    liststore = gtk.ListStore(str, str, str)
    for node_id_str in dad.bookmarks:
        # icon, node name, node id string
        liststore.append(["Red Cherry", dad.nodes_names_dict[long(node_id_str)], node_id_str])
    treeview = gtk.TreeView(liststore)
    treeview.set_headers_visible(False)
    treeview.set_reorderable(True)
    treeview.set_tooltip_text(_("Sort with Drag and Drop, Delete with the Delete Key"))
    treeviewselection = treeview.get_selection()
    def on_key_press_liststore(widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == "Delete":
            model, tree_iter = treeviewselection.get_selected()
            if tree_iter: model.remove(tree_iter)
    def on_mouse_button_clicked_liststore(widget, event):
        """Catches mouse buttons clicks"""
        if event.button != 1: return
        if event.type != gtk.gdk._2BUTTON_PRESS: return
        path_n_tvc = treeview.get_path_at_pos(int(event.x), int(event.y))
        if not path_n_tvc: return
        tree_path = path_n_tvc[0]
        dad_tree_path = dad.get_tree_iter_from_node_id(long(liststore[tree_path][2]))
        dad.treeview_safe_set_cursor(dad_tree_path)
    treeview.connect('key_press_event', on_key_press_liststore)
    treeview.connect('button-press-event', on_mouse_button_clicked_liststore)
    renderer_pixbuf = gtk.CellRendererPixbuf()
    renderer_text = gtk.CellRendererText()
    column = gtk.TreeViewColumn()
    column.pack_start(renderer_pixbuf, False)
    column.pack_start(renderer_text, True)
    column.set_attributes(renderer_pixbuf, stock_id=0)
    column.set_attributes(renderer_text, text=1)
    treeview.append_column(column)
    scrolledwindow = gtk.ScrolledWindow()
    scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolledwindow.add(treeview)
    content_area = dialog.get_content_area()
    content_area.pack_start(scrolledwindow)
    content_area.show_all()
    response = dialog.run()
    temp_bookmarks = []
    tree_iter = liststore.get_iter_first()
    while tree_iter != None:
        temp_bookmarks.append(liststore[tree_iter][2])
        tree_iter = liststore.iter_next(tree_iter)
    dialog.destroy()
    if response != gtk.RESPONSE_ACCEPT: return False
    dad.bookmarks = temp_bookmarks
    set_bookmarks_menu_items(dad)
    dad.ctdb_handler.pending_edit_db_bookmarks()
    return True

def set_object_highlight(inst, obj_highl):
    """Set the Highlight to obj_highl only"""
    if inst.highlighted_obj:
        inst.highlighted_obj.drag_unhighlight()
        inst.highlighted_obj = None
    if obj_highl:
        obj_highl.drag_highlight()
        inst.highlighted_obj = obj_highl
