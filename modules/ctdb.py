# -*- coding: UTF-8 -*-
#
#       ctdb.py
#
#       Copyright 2012 Giuseppe Penone <giuspen@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
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

import gtk
import os, sqlite3, xml.dom.minidom
import cons, support


class CTDBHandler:
    """Handler of the CherryTree DataBase"""

    def __init__(self, dad):
        """CherryTree DataBase boot"""
        self.dad = dad
    
    def get_table_db_tuple(self, table_element, node_id):
        """From table element to db tuple"""
        offset = table_element[0]
        table = table_element[1]
        justification = table_element[2]
        col_min = table_element['col_min']
        col_max = table_element['col_max']
        table_dom = xml.dom.minidom.Document()
        dom_iter = table_dom.createElement("table")
        table_dom.appendChild(dom_iter)
        for row in table_element['matrix']:
            dom_row = table_dom.createElement("row")
            dom_iter.appendChild(dom_row)
            for cell in row:
                dom_cell = table_dom.createElement("cell")
                dom_row.appendChild(dom_cell)
                text_iter = table_dom.createTextNode(cell)
                dom_cell.appendChild(text_iter)
        txt = table_dom.toxml()
        return (node_id, offset, justification, txt, col_min, col_max)
    
    def get_codebox_db_tuple(self, codebox_element, node_id):
        """From codebox element to db tuple"""
        offset = codebox_element[0]
        codebox = codebox_element[1]
        justification = codebox_element[2]
        txt = codebox['fill_text']
        syntax = codebox['syntax_highlighting']
        width = codebox['frame_width']
        height = codebox['frame_height']
        is_width_pix = codebox['width_in_pixels']
        do_highl_bra = codebox['highlight_brackets']
        do_show_linenum = codebox['show_line_numbers']
        return (node_id, offset, justification, txt, syntax,
                width, height, is_width_pix, do_highl_bra, do_show_linenum)
    
    def new_db(self, dbpath):
        """Create a new DataBase"""
        db = sqlite3.connect(dbpath)
        db.execute(cons.TABLE_NODE_CREATE)
        db.execute(cons.TABLE_CODEBOX_CREATE)
        db.execute(cons.TABLE_TABLE_CREATE)
        db.execute(cons.TABLE_IMAGE_CREATE)
        db.execute(cons.TABLE_CHILDREN_CREATE)
        db.execute(cons.TABLE_BOOKMARK_CREATE)
        db.commit()
        self.write_db_full(db)
        db.close()
    
    def write_db_bookmarks(self, db):
        """Write all the bookmarks in DB"""
        if not self.dad.bookmarks: return
        for bookmark_str in self.dad.bookmarks:
            bookmark_tuple = tuple(int(bookmark_str))
            db.execute('INSERT INTO bookmark VALUES(?)', bookmark_tuple)
        db.commit()
    
    def write_db_node(self, db, tree_iter, level, sequence):
        """Write a node in DB"""
        node_id = self.dad.treestore[tree_iter][3]
        name = self.dad.treestore[tree_iter][1]
        syntax = self.dad.treestore[tree_iter][4]
        tags = self.dad.treestore[tree_iter][6]
        is_ro = 1 if self.dad.treestore[tree_iter][7] else 0
        is_richtxt = 1 if syntax == cons.CUSTOM_COLORS_ID else 0
        has_codebox = 0
        has_table = 0
        has_image = 0
        has_children = 0
        curr_buffer = self.dad.treestore[tree_iter][2]
        start_iter = curr_buffer.get_start_iter()
        end_iter = curr_buffer.get_end_iter()
        if is_richtxt:
            # prepare xml dom node
            if "dom" in dir(self): del self.dom
            self.dom = xml.dom.minidom.Document()
            dom_iter = self.dom.createElement("node")
            self.dom.appendChild(dom_iter)
            # init attributes
            self.curr_attributes = {}
            for tag_property in cons.TAG_PROPERTIES: self.curr_attributes[tag_property] = ""
            # go!
            curr_iter = start_iter.copy()
            self.dad.xml_handler.rich_text_attributes_update(curr_iter, self.curr_attributes)
            tag_found = curr_iter.forward_to_tag_toggle(None)
            while tag_found:
                self.dad.xml_handler.rich_txt_serialize(dom_iter, start_iter, curr_iter, self.curr_attributes, dom=self.dom)
                if curr_iter.compare(end_iter) == 0: break
                else:
                    self.dad.xml_handler.rich_text_attributes_update(curr_iter, self.curr_attributes)
                    offset_old = curr_iter.get_offset()
                    start_iter.set_offset(offset_old)
                    tag_found = curr_iter.forward_to_tag_toggle(None)
                    if curr_iter.get_offset() == offset_old: break
            else:  self.dad.xml_handler.rich_txt_serialize(dom_iter, start_iter, curr_iter, self.curr_attributes, dom=self.dom)
            # time to retrieve the objects
            pixbuf_table_codebox_vector = self.dad.state_machine.get_embedded_pixbufs_tables_codeboxes(curr_buffer)
            # pixbuf_table_codebox_vector is [ [ "pixbuf"/"table"/"codebox", [offset, pixbuf, alignment] ],... ]
            codeboxes_tuples = []
            tables_tuples = []
            images_tuples = []
            for element in pixbuf_table_codebox_vector:
                if element[0] == "pixbuf":
                    self.pixbuf_element_to_xml(element[1], dom_iter, self.dom)
                elif element[0] == "table": tables_tuples.append(self.get_table_db_tuple(element[1], node_id))
                elif element[0] == "codebox": codeboxes_tuples.append(self.get_codebox_db_tuple(element[1], node_id))
            if codeboxes_tuples:
                has_codebox = 1
                for codebox_tuple in codeboxes_tuples:
                    db.execute('INSERT INTO codebox VALUES(?,?,?,?,?,?,?,?,?,?)', codebox_tuple)
            if tables_tuples:
                has_table = 1
                for table_tuple in tables_tuples:
                    db.execute('INSERT INTO table VALUES(?,?,?,?,?,?)', table_tuple)
            if images_tuples:
                has_image = 1
                for image_tuple in images_tuples:
                    db.execute('INSERT INTO image VALUES(?,?,?,?)', image_tuple)
            # retrieve xml text
            txt = self.dom.toxml()
        else: txt = start_iter.get_text(end_iter)
        node_tuple = (node_id, name, txt, syntax, tags,
                      is_ro, is_richtxt, has_codebox, has_table, has_image,
                      has_children, level, sequence)
        db.execute('INSERT INTO node VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', bookmark_tuple)
        db.commit()
    
    def write_db_full(self, db):
        """Write the whole DB"""
        tree_iter = self.dad.treestore.get_iter_first()
        sequence = 0
        while tree_iter != None:
            sequence += 1
            self.write_db_node(db, tree_iter, 1, sequence)
            tree_iter = self.dad.treestore.iter_next(tree_iter)
        self.write_db_bookmarks(db)
