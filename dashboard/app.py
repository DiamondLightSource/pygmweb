import seaborn as sns
from faicons import icon_svg
import matplotlib.pyplot as plt
# Import data from shared.py
import micropip
micropip.install("https://github.com/patrickwang27/pgmcomponents/releases/download/1.0/pgmcomponents-1.0-py3-none-any.whl")
from shared import app_dir, df
from pathlib import Path
from shiny import App, reactive, render, ui
app_dir = Path(__file__).parent
from pgmcomponents.elements import *
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.accordion(
            ui.accordion_panel(
                "Beam Configurations",
                ui.input_slider("beam_height", "Beam Height (mm)", 0, 60,step=0.1, value=5),
                ui.input_slider("beam_width","Beam Width (mm)",0,60,value=5,step=0.1),
            ),
            open=True
        ),
        ui.accordion(
            ui.accordion_panel(
                "Mirror Configurations",
                ui.input_numeric('mirror_height', "Mirror Height (mm)", 20,min=0),
                ui.input_numeric("mirror_length", "Mirror Length/Tangential (mm)", 150, min=0),
                ui.input_numeric('mirror_width', "Mirror Width/Sagittal (mm)", 45, min=0),
            ),
            open=False
        ),
        ui.accordion(
            ui.accordion_panel(
                "Grating Configurations",
                ui.input_numeric('grating_height', "Grating Height (mm)", 20, min=0),
                ui.input_numeric('grating_length', "Grating Length (mm)", 150, min=0),
                ui.input_numeric('grating_width', "Grating Width (mm)", 45, min=0),
            ),
            open=False
        ),
        ui.accordion(
            ui.accordion_panel(
                "Offsets Configurations",
                ui.img(src='pgm.png'),
                ui.input_numeric('beam_vertical_offset', "Beam Vertical Offset (mm) $b$" , -13, min=-100, max=100),
                ui.input_numeric('mirror_horizontal_offset', "Mirror Horizontal Offset $a$ (mm)", 0, min=-100, max=100),
                ui.input_checkbox("calculate_offsets", "Calculate Offsets Automatically", value=True),
                ui.input_numeric('mirror_vertical_offset', "Mirror Vertical Offset $c$ (mm)", 13, min=-100, max=100),
                ui.input_numeric('mirror_axis_horizontal_offset', "Mirror Axis Horizontal Offset $h$ (mm)", 0, min=-100, max=100),
                ui.input_numeric('mirror_axis_vertical_offset', "Mirror Axis Vertical Offset $v$ (mm)", 6.5, min=-100, max=100),
            ), open=False),
        title="PGM Configurations"),
    ui.layout_column_wrap(
        ui.value_box(
            "Energy (eV)",
            ui.input_numeric("energy", "", 500, min=0, step=10),
        ),
        ui.value_box(
            "Order",
            ui.input_slider("order", "", 1, 10, value=1),
        ),
        ui.value_box(
            r'\(\mathit{c_{ff}}\)',
            ui.input_numeric("c_ff", "", 1.4, min=1, max=15, step=0.1),
        ),
        ui.value_box(
            "Line Density (l/mm)",
            ui.input_numeric("line_density", "", 400, min=0, max=3600),
        ),
        fill=False,
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Side View"),
            ui.output_plot("top_view"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Footprint View"),
            ui.output_plot("side_view"),
            full_screen=True,
        ),
    ),
    ui.include_css(app_dir / "styles.css"),
    ui.tags.head(ui.tags.script(src="https://polyfill.io/v3/polyfill.min.js?features=es6"),
    ui.tags.script(id="MathJax-script", src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js")),
    title="Plane Grating Monochromator Simulator",
    fillable=True,
)


def server(input, output, session):
    @reactive.calc
    def filtered_df():
        filt_df = df[df["species"].isin(input.species())]
        filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
        return filt_df

    @render.text
    def count():
        return filtered_df().shape[0]

    @render.text
    def bill_length():
        return f"{filtered_df()['bill_length_mm'].mean():.1f} mm"

    @render.text
    def bill_depth():
        return f"{filtered_df()['bill_depth_mm'].mean():.1f} mm"

    @render.plot
    def top_view():
        fig, ax = plt.subplots()
        pgm = PGM(grating=Grating(), mirror=Plane_Mirror())
        pgm.beam_height = input.beam_height()
        pgm.energy=float(input.energy())
        pgm.grating.order=int(input.order())
        pgm.cff=float(input.c_ff())
        pgm.grating.line_density=float(input.line_density())
        pgm.mirror.dimensions = [float(input.mirror_length()),float(input.mirror_width()),float(input.mirror_height())]
        pgm.grating.dimensions=[float(input.grating_length()),float(input.grating_width()),float(input.grating_height())]
        pgm.beam_offset=float(input.beam_vertical_offset())
        pgm.mirror.hoffset=float(input.mirror_horizontal_offset())
        pgm.mirror.voffset=float(input.mirror_vertical_offset())
        pgm.mirror.axis_hoffset=float(input.mirror_axis_horizontal_offset())
        pgm.mirror.axis_voffset=float(input.mirror_axis_vertical_offset())
        _ = pgm.mirror.compute_corners()
        _ = pgm.grating.compute_corners()
        pgm.generate_rays()
        pgm.grating.compute_angles()
        pgm.set_theta()
        pgm.draw_sideview(ax)
        ax.set_xlim(-250,250)
        ax.set_ylim(-100,100)
        ax.set_aspect("equal")
        return fig

    @render.plot
    def side_view():
        fig, ax = plt.subplots()
        pgm = PGM(grating=Grating(), mirror=Plane_Mirror())
        pgm.beam_height = input.beam_height()
        pgm.energy=float(input.energy())
        pgm.grating.order=int(input.order())
        pgm.cff=float(input.c_ff())
        pgm.grating.line_density=float(input.line_density())
        pgm.mirror.dimensions = [float(input.mirror_length()),float(input.mirror_width()),float(input.mirror_height())]
        pgm.grating.dimensions=[float(input.grating_length()),float(input.grating_width()),float(input.grating_height())]
        pgm.beam_offset=float(input.beam_vertical_offset())
        pgm.mirror.hoffset=float(input.mirror_horizontal_offset())
        pgm.mirror.voffset=float(input.mirror_vertical_offset())
        pgm.mirror.axis_hoffset=float(input.mirror_axis_horizontal_offset())
        pgm.mirror.axis_voffset=float(input.mirror_axis_vertical_offset())
        _ = pgm.mirror.compute_corners()
        _ = pgm.grating.compute_corners()
        pgm.generate_rays()
        pgm.grating.compute_angles()
        pgm.set_theta()
        #pgm.draw_sideview(ax)
        #ax.set_xlim(-250,250)
        #ax.set_ylim(-100,100)
        ax.set_aspect("equal")
        pgm.draw_topview(ax)
        #ax.set_xlim(-250,250)
        #ax.set_ylim(-100,100)
        #ax.set_aspect("equal")
        return fig


app = App(app_ui, server, static_assets=app_dir / "static",)
