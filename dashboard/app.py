from faicons import icon_svg
from pathlib import Path
from shiny import App, reactive, render, ui
app_dir = Path(__file__).parent
from pyplanemono_minimal.elements import *
from pyplanemono_minimal.geometry import calc_beam_size
import plotly.graph_objects as go
from shinywidgets import output_widget, render_plotly

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
                ui.tooltip(ui.input_checkbox("calc_beam_height", "Calculate Beam Height Automatically", value=False),
                           'This calculates the vertical beam size at the grating and mirror from an undulator source for the given PGM energy.'),
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
    

    ui.card(ui.card_header("Footprint View"),output_widget("top_view"),full_screen=True, fill=True),
    ui.card(ui.card_header("Side View"),output_widget("side_view"),full_screen=True, fill=True),

    ui.include_css(app_dir / "styles.css"),
    ui.tags.head(ui.tags.script(src="https://polyfill.io/v3/polyfill.min.js?features=es6"),
    ui.tags.script(id="MathJax-script", src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js")),
    title="Plane Grating Monochromator Simulator",
    fillable=True
)


def server(input, output, session):

    @render_plotly
    def top_view():
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
        pgm.grating.compute_angles()
        pgm.set_theta()
        m_corners = pgm.mirror_corners()
        m_corners = np.array(m_corners)
        grating_corners = np.array(pgm.grating_corners())
        mirror_corners = np.array(pgm.mirror_corners())
        pgm.generate_rays()
        _, mirror_int_1, grating_int_1 =  pgm.propagate(pgm.rays[1])
        _, mirror_int_2, grating_int_2 =  pgm.propagate(pgm.rays[2])
        _, mirror_int_3, grating_int_3 =  pgm.propagate(pgm.rays[3])
        _, mirror_int_4, grating_int_4 =  pgm.propagate(pgm.rays[4])

        mirror_intercepts = [
            mirror_int_1[0].to_point(),
            mirror_int_2[0].to_point(),
            mirror_int_3[0].to_point(),
            mirror_int_4[0].to_point()
        ]

        grating_intercepts = [
            grating_int_1[0].to_point(),
            grating_int_2[0].to_point(),
            grating_int_3[0].to_point(),
            grating_int_4[0].to_point()
        ]

        mirror_footprint_width, mirror_footprint_height = pgm.calc_footprint_size(mirror_intercepts)
        grating_footprint_width, grating_footprint_height = pgm.calc_footprint_size(grating_intercepts)

        mirr_footprint_corners = np.array([
            [mirror_int_2[0].z, mirror_int_3[0].x],
            [mirror_int_1[0].z, mirror_int_3[0].x],
            [mirror_int_1[0].z, mirror_int_4[0].x],
            [mirror_int_2[0].z, mirror_int_4[0].x]
        ])

        grating_footprint_corners = np.array([
            [grating_int_2[0].z, grating_int_3[0].x],
            [grating_int_1[0].z, grating_int_3[0].x],
            [grating_int_1[0].z, grating_int_4[0].x],
            [grating_int_2[0].z, grating_int_4[0].x]
        ])

        offset = 0.5*(pgm.mirror._width() + pgm.grating._width())* np.array([
            [0,1],
            [0,1],
            [0,1],
            [0,1]
        ])

        grating_corners = grating_corners + offset
        grating_footprint_corners = grating_footprint_corners + offset

        fig = go.Figure(layout={'showlegend':False, 
                                'xaxis':{'range':(min(mirror_corners[:,0])-50,max(grating_corners[:,0])+50)},
                                'yaxis':{'range':(min(mirror_corners[:,1])-100,max(grating_corners[:,1])+50)}, 
                                'height':400})
        fig.add_trace(go.Scatter(x=mirror_corners[:,0], y=mirror_corners[:,1],fill='toself',fillcolor='red',line={"color":'red'}, marker={'size':0}, name='Mirror'))
        fig.add_trace(go.Scatter(x=grating_corners[:,0], y=grating_corners[:,1],fill='toself',fillcolor='blue',line={"color":'blue'}, marker={'size':0}, name='Grating'))
        fig.add_trace(go.Scatter(x=mirr_footprint_corners[:,0], y=mirr_footprint_corners[:,1],fill='toself',fillcolor='green',line={"color":'green'}, marker={'size':0}, name='Beam Footprint on Mirror'))
        fig.add_trace(go.Scatter(x=grating_footprint_corners[:,0], y=grating_footprint_corners[:,1],fill='toself',fillcolor='green',line={"color":'green'}, marker={'size':0}, name='Beam Footprint on Grating'))
        return fig

    @render_plotly
    def side_view():
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
        mirror_corners = pgm.mirror.compute_corners()
        grating_corners = pgm.grating.compute_corners()
        rays = pgm.generate_rays()
        _ = pgm.propagate(pgm.rays)
        mirror_z = np.array(
            [mirror_corners[i][2] for i in [4,6,2,0,4]]
        )
        mirror_x = np.array(
            [mirror_corners[i][1] for i in [4,6,2,0,4]]
        )

        grating_z = np.array(
            [grating_corners[i][2] for i in [4,6,2,0,4]]
        )
        grating_x = np.array(
            [grating_corners[i][1] for i in [4,6,2,0,4]]
        )
        ray1z = [pgm.rays[0].position.list[2],
                pgm.mirror_intercept[0].z,
                pgm.grating_intercept[0].z,
                1000]

        ray1x = [pgm.rays[0].position.list[1],
                pgm.mirror_intercept[0].y,
                pgm.grating_intercept[0].y,
                0]
        ray2z = [pgm.rays[1].position.list[2],
                pgm.mirror_intercept[1].z,
                pgm.grating_intercept[1].z,
                1000]

        ray2x = [pgm.rays[1].position.list[1],
                pgm.mirror_intercept[1].y,
                pgm.grating_intercept[1].y,
                pgm.grating_intercept[1].y + 1000*pgm.rays[1].vector[1]]

        ray3z = [pgm.rays[2].position.list[2],
                pgm.mirror_intercept[2].z,
                pgm.grating_intercept[2].z,
                1000]

        ray3x = [pgm.rays[2].position.list[1],
                pgm.mirror_intercept[2].y,
                pgm.grating_intercept[2].y,
                pgm.grating_intercept[2].y + 1000*pgm.rays[2].vector[1]]
        

        fig = go.Figure(layout={'showlegend':False, 'xaxis':{'range':(min(ray3z[1:])-50,max(ray2z[1:-1])+50),}, 'height':800})
        fig.add_trace(go.Scatter(x=mirror_z, y=mirror_x,fill='toself',fillcolor='red',line={"color":'red'}, marker={'size':0}, name='Mirror'))
        fig.add_trace(go.Scatter(x=grating_z, y=grating_x,fill='toself',fillcolor='blue',line={"color":'blue'}, marker={'size':0}, name='Grating')) #mode lines if to hide vertices
        fig.update_yaxes(scaleanchor="x",scaleratio=1,)

        fig.add_trace(go.Scatter(x=ray1z, y = ray1x, line={'color':'green', 'width':1.5}))
        fig.add_trace(go.Scatter(x=ray2z, y = ray2x, line={'color':'green', 'width':1.5}))
        fig.add_trace(go.Scatter(x=ray3z, y = ray3x, line={'color':'green', 'width':1.5}))

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
                ui.input_numeric('electron_size', " Vertical Electron Beam Size (um)", 50, min=0),
                ui.input_numeric('electron_divergence', "Electron Beam Vertical Divergence (urad)", 20, min=0),
                ui.input_numeric('distance_to_mirror', "Distance to Image Plane (m)", 15, min=0),
                ui.input_numeric('length_of_id', "Length of ID (m)", 2, min=0),
                ui.input_numeric('num_of_sigmas', "Number of Sigmas", 5, min=0),
                ui.output_text("beam_size_mirror", "Vertical Beam Height Mirror:"),)
        else:
            return ui.input_numeric("beam_height", "Beam Height (mm)", 5,step=0.1,min=0, max=100)


app = App(app_ui, server, static_assets=app_dir / "static",)
