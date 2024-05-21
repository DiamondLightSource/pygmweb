import seaborn as sns
from faicons import icon_svg
import matplotlib.pyplot as plt
from pathlib import Path
from shiny import App, reactive, render, ui
app_dir = Path(__file__).parent
from pyplanemono_minimal.pyplanemono_minimal.elements import *
from pyplanemono_minimal.geometry import calc_beam_size
import plotly.express as px
from shinywidgets import output_widget, render_widget, render_plotly


H = 6.62607015e-34
E = 1.602176634e-19
C = 299792458
to_wavelength = lambda x: H*C/(E*x)
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.layout_column_wrap(
        ui.card(
            "Energy (eV)",
            ui.input_numeric("energy", "", 500, min=0, step=10),
            fill=False
        ),
        ui.card(
            "Order",
            ui.input_slider("order", "", 1, 10, value=1),
            fill=False
        ),
        ui.card(
            r'\(\mathit{c_{ff}}\)',
            ui.input_numeric("c_ff", "", 1.4, min=1, max=15, step=0.1),
            fill=False
        ),
        ui.card(
            "Line Density (l/mm)",
            ui.input_numeric("line_density", "", 400, min=0, max=3600),
            fill=False
        ),
        fill=False,
    ),
        ui.accordion(
            ui.accordion_panel(
                "Beam Configurations",
                ui.input_checkbox("calc_beam_height", "Calculate Beam Height Automatically", value=False),
                ui.output_ui('beam_height_calc_ui'),
                ui.input_numeric("beam_width","Beam Width (mm)",5,step=0.1,min=0, max=100),
            ),
            open=True
        ),
        ui.accordion(
            ui.accordion_panel(
                "Mirror Configurations",
                ui.input_numeric('mirror_height', "Mirror Height (mm)", 40,min=0),
                ui.input_numeric("mirror_length", "Mirror Length/Tangential (mm)", 450, min=0),
                ui.input_numeric('mirror_width', "Mirror Width/Sagittal (mm)", 40, min=0),
            ),
            open=False
        ),
        ui.accordion(
            ui.accordion_panel(
                "Grating Configurations",
                ui.input_numeric('grating_height', "Grating Height (mm)", 40, min=0),
                ui.input_numeric('grating_length', "Grating Length (mm)", 150, min=0),
                ui.input_numeric('grating_width', "Grating Width (mm)", 45, min=0),
            ),
            open=False
        ),
        ui.accordion(
            ui.accordion_panel(
                "Offsets Configurations",
                ui.img(src='pgm.png'),
                ui.input_numeric('beam_vertical_offset', "Beam Vertical Offset (mm) \(b\)" , -13, min=-100, max=100),
                ui.input_numeric('mirror_horizontal_offset', "Mirror Horizontal Offset \(a\) (mm)", 0, min=-100, max=100),
                ui.input_checkbox("calculate_offsets", "Calculate Offsets Automatically", value=True),
                ui.input_numeric('mirror_vertical_offset', "Mirror Vertical Offset \(c\) (mm)", 13, min=-100, max=100),
                ui.input_numeric('mirror_axis_horizontal_offset', "Mirror Axis Horizontal Offset \(h\) (mm)", 0, min=-100, max=100),
                ui.input_numeric('mirror_axis_vertical_offset', "Mirror Axis Vertical Offset \(v\) (mm)", 6.5, min=-100, max=100),
            ), open=False),
        title="PGM Configurations"),
    

    ui.card(ui.card_header("Side View"),ui.output_plot("top_view", brush=True, inline=False, fill=False),full_screen=True, fill=True),
    ui.card(ui.card_header("Side View"),ui.output_plot("side_view", brush=True, inline=False, fill=False),full_screen=True, fill=True),

    ui.include_css(app_dir / "styles.css"),
    ui.tags.head(ui.tags.script(src="https://polyfill.io/v3/polyfill.min.js?features=es6"),
    ui.tags.script(id="MathJax-script", src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js")),
    title="Plane Grating Monochromator Simulator",
    fillable=True
)


def server(input, output, session):

    @render.plot
    def top_view():
        fig, ax = plt.subplots(figsize=(10,10))
        pgm = PGM(grating=Grating(), mirror=Plane_Mirror())
        if input.calc_beam_height():
            beamsize = calc_beam_size(float(input.electron_size()), 
                                  float(input.electron_divergence()), 
                                  to_wavelength(float(input.energy()))/1E-9, 
                                  float(input.distance_to_mirror()), 
                                  float(input.length_of_id()), 
                                  num_of_sigmas = float(input.num_of_sigmas()))
            pgm.beam_height = beamsize
        else:
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
        ax.set_xlim(-200,100)
        ax.set_ylim(-60,60)
        ax.set_aspect("equal")
        #pgm.draw_topview(ax2)
        return fig

    @render.plot
    def side_view():
        fig, ax = plt.subplots()
        pgm = PGM(grating=Grating(), mirror=Plane_Mirror())
        if input.calc_beam_height():
            beamsize = calc_beam_size(float(input.electron_size()), 
                                  float(input.electron_divergence()), 
                                  to_wavelength(float(input.energy()))/1E-9, 
                                  float(input.distance_to_mirror()), 
                                  float(input.length_of_id()), 
                                  num_of_sigmas = float(input.num_of_sigmas()))
            pgm.beam_height = beamsize
        else:
            pgm.beam_height = input.beam_height()
        
        pgm.beam_width = input.beam_width()
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
        ax.get_legend().set_visible(False)

        #ax.set_xlim(-250,250)
        #ax.set_ylim(-100,100)
        ax.set_aspect("equal")
        return fig
    
    @render.text
    def beam_size_mirror():
        
        beamsize = calc_beam_size(float(input.electron_size()), 
                                  float(input.electron_divergence()), 
                                  to_wavelength(float(input.energy()))/1E-9, 
                                  float(input.distance_to_mirror()), 
                                  float(input.length_of_id()), 
                                  num_of_sigmas = float(input.num_of_sigmas()))
        return f"Beam Height : {beamsize:.3f} mm"
    
    @render.ui
    @reactive.event(input.calc_beam_height)
    def beam_height_calc_ui():
        if input.calc_beam_height():
            return ui.TagList(
                "This calculates the vertical beam size at the grating and mirror from an undulator source for the given PGM energy.",
                ui.input_numeric('electron_size', " Vertical Electron Beam Size (um)", 50, min=0),
                ui.input_numeric('electron_divergence', "Electron Beam Vertical Divergence (urad)", 20, min=0),
                ui.input_numeric('distance_to_mirror', "Distance to Image Plane (m)", 15, min=0),
                ui.input_numeric('length_of_id', "Length of ID (m)", 2, min=0),
                ui.input_numeric('num_of_sigmas', "Number of Sigmas", 5, min=0),
                ui.output_text("beam_size_mirror", "Vertical Beam Height Mirror:"),)
        else:
            return ui.input_numeric("beam_height", "Beam Height (mm)", 5,step=0.1,min=0, max=100)


app = App(app_ui, server, static_assets=app_dir / "static",)
