#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AstroPhoto picture information border generator.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#
# Heavily inspired by Astrophotography plugins for GIMP 2.10 by Georg Hennig.
# http://www.hennigbuam.de/georg/gimp.html
# https://github.com/funxiun/gimp-plugin-astronomy
#
# Developed by following the excellent "Python Plug-Ins" tutorial GIMP developer documentation.
# https://testing.developer.gimp.org/resource/writing-a-plug-in/tutorial-python/


import gi
gi.require_version('Babl', '0.1')
from gi.repository import Babl
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk


PROCEDURE_NAME = "plug-in-porridge-astrophoto-info-border"


class AstroPhotoBorder(Gimp.PlugIn):
  def do_query_procedures(self):
    return [PROCEDURE_NAME]

  def do_create_procedure(self, name):
    if name != PROCEDURE_NAME:
      return None
    return create_procedure(self, name)


def create_procedure(plugin, name):
  Babl.init() # to get defaults for color formal args

  p = Gimp.ImageProcedure.new(plugin, name, Gimp.PDBProcType.PLUGIN, astrophoto_border_run, None)
  p.set_sensitivity_mask( # need an image, number of selected drawables is irrelevant
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
      | Gimp.ProcedureSensitivityMask.DRAWABLE
      | Gimp.ProcedureSensitivityMask.DRAWABLES)
  p.set_menu_label("Image _info border")
  p.set_attribution("Marcin Owsiany", "Copyright 2026 Marcin Owsiany", "2026-02-23")
  p.add_menu_path("<Image>/Astrophotography")
  p.set_documentation(
    "Adds an information border to an image",
    "Adds a border around an image with six pieces of informative text at the bottom: {left, middle, right}x{1st line, 2nd line}.", None)

  p.add_int_argument("border-size-inner", "Inner border size (px)", None, 1, 100, 4, GObject.ParamFlags.READWRITE)
  p.add_color_argument("border-color-inner", "Inner border color", None, False, Gegl.Color.new("#ffffff"), GObject.ParamFlags.READWRITE)

  p.add_int_argument("border-size-outer", "Outer border size (px)", None, 1, 100, 20, GObject.ParamFlags.READWRITE)
  p.add_color_argument("border-color-outer", "Outer border color", None, False, Gegl.Color.new("#303030"), GObject.ParamFlags.READWRITE)

  p.add_font_argument("font", "Font", None, False, None, True, GObject.ParamFlags.READWRITE)
  p.add_color_argument("font-color", "Font color", None, False, Gegl.Color.new("#ffffff"), GObject.ParamFlags.READWRITE)

  add_field(p, label_suffix="l1", desc_prefix="Left 1st line", desc_default="Telescope, camera type", val_default=22)
  add_field(p, label_suffix="l2", desc_prefix="Left 2nd line", desc_default="Mount, etc", val_default=14)
  add_field(p, label_suffix="m1", desc_prefix="Middle 1st line", desc_default="Object name", val_default=24)
  add_field(p, label_suffix="m2", desc_prefix="Middle 2nd line", desc_default="Exposure, filters", val_default=14)
  add_field(p, label_suffix="r1", desc_prefix="Right 1st line", desc_default="Author's name", val_default=22)
  add_field(p, label_suffix="r2", desc_prefix="Right 2nd line", desc_default="Date, location", val_default=14)

  return p


def add_field(p, label_suffix, desc_prefix, desc_default, val_default):
    p.add_string_argument("text-"+label_suffix, desc_prefix+" text", None, desc_default, GObject.ParamFlags.READWRITE)
    p.add_int_argument("font-size-"+label_suffix, desc_prefix+" font size ", None, 1, 1000, val_default, GObject.ParamFlags.READWRITE)
    p.add_unit_argument("font-unit-"+label_suffix, desc_prefix+" font unit", None, True, False, Gimp.Unit.point(), GObject.ParamFlags.READWRITE)


def show_dialog(procedure, config):
    import os.path
    GimpUi.init(os.path.basename(__file__))

    dialog = GimpUi.ProcedureDialog.new(procedure, config, "AstroPhoto Info Border")
    try:
      for pos in ["inner", "outer"]:
        box = dialog.fill_box("box-border-"+pos, ["border-size-"+pos, "border-color-"+pos])
        box.set_orientation(Gtk.Orientation.HORIZONTAL)

      dialog.fill_box("font-box", ["font", "font-color"]).set_orientation(Gtk.Orientation.HORIZONTAL)

      for row in ["1", "2"]:
        for col in ["l", "m", "r"]:
          dialog.fill_box("size-box-"+col+row, ["font-size-"+col+row, "font-unit-"+col+row]).set_orientation(Gtk.Orientation.HORIZONTAL)
        dialog.fill_box("size-row-"+row, ["size-box-l"+row, "size-box-m"+row, "size-box-r"+row]).set_orientation(Gtk.Orientation.HORIZONTAL)
        dialog.fill_box("text-row-"+row, ["text-l"+row, "text-m"+row, "text-r"+row]).set_orientation(Gtk.Orientation.HORIZONTAL)

      dialog.fill(["box-border-inner", "box-border-outer", "font-box", "text-row-1", "size-row-1", "text-row-2", "size-row-2"])

      return dialog.run()
    finally:
      dialog.destroy()


def astrophoto_border_run(procedure, run_mode, image, drawables, config, data):
  if not image:
    return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error(f"Procedure '{PROCEDURE_NAME}' works with images only."))

  if run_mode == Gimp.RunMode.INTERACTIVE:
    if not show_dialog(procedure, config):
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)

  inner_width = config.get_property('border-size-inner')
  outer_width = config.get_property('border-size-outer')

  image.undo_group_start()
  try:
    for l in image.get_layers():
      l.add_alpha()
    orig_color = Gimp.context_get_foreground()
    orig_width, orig_height = image.get_width(), image.get_height()
    text_top = orig_height + inner_width + outer_width
    text_inter_row_padding = outer_width
    middle_width = int(image.get_width()/2)

    Gimp.context_set_foreground(config.get_property('font-color'))
  
    text_l1_layer = add_text_field_layer(image, config, 'l1', Gimp.TextJustification.LEFT)
    text_l2_layer = add_text_field_layer(image, config, 'l2', Gimp.TextJustification.LEFT)
    l_bottom = place_text_field_layers(text_l1_layer, text_l2_layer, 0, 0, text_top, text_inter_row_padding)

    text_m1_layer = add_text_field_layer(image, config, 'm1', Gimp.TextJustification.CENTER)
    text_m2_layer = add_text_field_layer(image, config, 'm2', Gimp.TextJustification.CENTER)
    text_m1_x = middle_width - int(text_m1_layer.get_width()/2)
    text_m2_x = middle_width - int(text_m2_layer.get_width()/2)
    m_bottom = place_text_field_layers(text_m1_layer, text_m2_layer, text_m1_x, text_m2_x, text_top, text_inter_row_padding)

    text_r1_layer = add_text_field_layer(image, config, 'r1', Gimp.TextJustification.RIGHT)
    text_r2_layer = add_text_field_layer(image, config, 'r2', Gimp.TextJustification.RIGHT)
    text_r1_x = orig_width - text_r1_layer.get_width()
    text_r2_x = orig_width - text_r2_layer.get_width()
    r_bottom = place_text_field_layers(text_r1_layer, text_r2_layer, text_r1_x, text_r2_x, text_top, text_inter_row_padding)

    text_bottom = max(l_bottom, m_bottom, r_bottom)

    image.resize(orig_width+2*inner_width, orig_height+2*inner_width, inner_width, inner_width)
    inner_border_layer = add_filled_layer(image, config.get_property('border-color-inner'), "inner border")

    image.resize(image.get_width()+2*outer_width, text_bottom+2*inner_width+2*outer_width, outer_width, outer_width)
    add_filled_layer(image, config.get_property('border-color-outer'), "Info border")

    # Order is important: we want to merge each layer to the bottom one (outer border layer).
    for l in [
      inner_border_layer,
      text_r2_layer, text_r1_layer,
      text_m2_layer, text_m1_layer,
      text_l2_layer, text_l1_layer]:
      image.merge_down(l, Gimp.MergeType.EXPAND_AS_NECESSARY)

    Gimp.context_set_foreground(orig_color)
  finally:
    image.undo_group_end()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


def add_text_field_layer(image, config, suffix, justify):
  l = Gimp.TextLayer.new(
    image,
    config.get_property('text-'+suffix),
    config.get_property('font'),
    config.get_property('font-size-'+suffix),
    config.get_property('font-unit-'+suffix))
  image.insert_layer(l, None, len(image.get_layers()))
  l.set_justification(justify)
  return l


def place_text_field_layers(row1_layer, row2_layer, row1_x, row2_x, text_top, padding):
  row2_y = text_top + row1_layer.get_height() + padding
  row1_layer.set_offsets(row1_x, text_top)
  row2_layer.set_offsets(row2_x, row2_y)
  return row2_y + row2_layer.get_height()


def add_filled_layer(image, color, name):
  l = Gimp.Layer.new(image, name, image.get_width(), image.get_height(), Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
  image.insert_layer(l, None, len(image.get_layers()))
  image.set_selected_layers([l])
  Gimp.context_set_foreground(color)
  l.fill(Gimp.FillType.FOREGROUND)
  return l


if __name__ == '__main__':
  import sys
  Gimp.main(AstroPhotoBorder.__gtype__, sys.argv)
