from faicons import icon_svg
from pathlib import Path
from shiny import App, reactive, render, ui
app_dir = Path(__file__).parent
from pyplanemono_minimal.elements import *
from pyplanemono_minimal.geometry import calc_beam_size
import plotly.graph_objects as go
from shinywidgets import output_widget, render_plotly
from configparser import ConfigParser
from shiny.types import FileInfo
import asyncio
import io

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
            ui.input_slider("order", "", 0, 10, value=1),
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
                ui.tooltip(ui.input_checkbox("calc_beam_height", "Calculate ID Beam Height", value=False),
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
                ui.input_numeric("mirror_length", "Mirror Length (mm)", 450, min=0),
                ui.input_numeric('mirror_width', "Mirror Width (mm)", 40, min=0),
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
                "Offsets Configurations" ,
                ui.tags.a("Offsets definitions", href="https://pgmweb.diamond.ac.uk/tutorial.html#offsets", target="_blank"),
                ui.input_numeric('beam_vertical_offset', "Beam Vertical Offset \(b\) (mm) " , -13, min=-100, max=100),
                ui.input_numeric('mirror_horizontal_offset', "Mirror Horizontal Offset \(a\) (mm)", 0, min=-100, max=100),
                ui.input_checkbox("calculate_offsets", "Calculate Offsets Automatically", value=False),
                ui.output_ui('offset_calc_ui'),
            ), open=True),
        ui.accordion(
            ui.accordion_panel("Export and Import",
                ui.input_text("export_filename", "Export Filename", "pgm_configurations.pgm"),
                ui.download_button("export_pgm","Export Current PGM"),
                ui.input_file("import_pgm","Upload Configuration File", accept=".pgm", multiple=False),
                ui.input_action_button("import_button", "Import")),
                
                open=False),

        title="PGM Configurations"),

        


    ui.card(ui.card_header("Footprint View", "  ", ui.tooltip(icon_svg('circle-info'),"Beam footprint size", id='beamfootprint_tooltip')),output_widget("top_view"),full_screen=True),
    ui.card(ui.card_header("Side View", " ", ui.tooltip(icon_svg('circle-info'),ui.output_ui('side_view_angles'), id='angle_tooltip')),output_widget("side_view"),full_screen=True, fill=False),

    ui.include_css(app_dir / "styles.css"),
    ui.tags.head(ui.tags.script(src="https://polyfill.io/v3/polyfill.min.js?features=es6"),
    ui.tags.script(id="MathJax-script", src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"),
    ui.tags.script("""var inputs = document.querySelectorAll('input[type=number]');
for (var i = 0; i < inputs.length; i++) {
    inputs[i].addEventListener('wheel', function(e){
        e.preventDefault();
    });
}""")),
    title="PGMweb",
    fillable=True
)


def server(input, output, session):

    @render.text
    def beam_size_mirror():
        
        beamsize = calc_beam_size(float(input.electron_size()), 
                                  float(input.electron_divergence()), 
                                  to_wavelength(float(input.energy()))/1E-9, 
                                  float(input.distance_to_mirror()), 
                                  float(input.length_of_id()), 
                                  num_of_sigmas = float(input.num_of_sigmas()))
        return rf"Beam Height : {beamsize:.3f} mm"

    @render.ui
    @reactive.event(input.calc_beam_height)
    def beam_height_calc_ui():
        if input.calc_beam_height():
            return ui.TagList(
                ui.input_numeric('electron_size', " Vertical Electron Beam Size RMS (um)", 50, min=0),
                ui.input_numeric('electron_divergence', "Vertical Electron Beam Divergence RMS (urad)", 20, min=0),
                ui.input_numeric('distance_to_mirror', "Distance to Image Plane (m)", 15, min=0),
                ui.input_numeric('length_of_id', "Length of ID (m)", 2, min=0),
                ui.input_numeric('num_of_sigmas', "Number of Sigmas", 5, min=0),
                ui.output_text("beam_size_mirror"),)
        else:
            return ui.input_numeric("beam_height", "Beam Height (mm)", 5,step=0.1,min=0, max=100)

    @render.ui
    def voffset_out():
        return ui.TagList(
            ui.tags.div(f"Mirror Vertical Offset \(c\) : {-1*float(input.beam_vertical_offset())} mm"),
            ui.tags.script("MathJax.typesetPromise();"))    
    @render.ui
    def axis_hoffset_out():
        return ui.TagList(
            ui.tags.div(f"Mirror Axis Horizontal Offset \(h\) : 0 mm"),
            ui.tags.script("MathJax.typesetPromise();"))
    
    
    @render.ui
    def axis_voffset_out():
        return ui.TagList(
            ui.tags.div(f"Mirror Axis Vertical Offset \(v\) : {-1*float(input.beam_vertical_offset())/2} mm"),
            ui.tags.script("MathJax.typesetPromise();"))
    

    
    @render.ui
    @reactive.event(input.calculate_offsets)
    def offset_calc_ui():
        if input.calculate_offsets():
            return ui.TagList(
                ui.output_ui("voffset_out"),
                ui.output_ui('axis_hoffset_out'),
                ui.output_ui('axis_voffset_out'), 
                )
        else:
            return ui.TagList(
                ui.input_numeric(r'mirror_vertical_offset', "Mirror Vertical Offset \(c\) (mm)", 13, min=-100, max=100),
                ui.input_numeric(r'mirror_axis_horizontal_offset', "Mirror Axis Horizontal Offset \(h\) (mm)", 0, min=-100, max=100),
                ui.input_numeric(r'mirror_axis_vertical_offset', "Mirror Axis Vertical Offset \(v\) (mm)", 6.5, min=-100, max=100),
                ui.tags.script("MathJax.typesetPromise();")
            )
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
        
        if input.calculate_offsets():
            b = float(input.beam_vertical_offset())
            pgm.beam_offset = b
            pgm.mirror.hoffset = float(input.mirror_horizontal_offset())
            pgm.mirror.axis_voffset = -1*b/2
            pgm.mirror.voffset = -1*b
            pgm.mirror.axis_hoffset = 0.
        else:
            pgm.beam_offset = float(input.beam_vertical_offset())
            pgm.mirror.hoffset = float(input.mirror_horizontal_offset())
            pgm.mirror.axis_voffset = float(input.mirror_axis_vertical_offset())
            pgm.mirror.voffset = float(input.mirror_vertical_offset())
            pgm.mirror.axis_hoffset = float(input.mirror_axis_horizontal_offset())
        
        pgm.beam_width = input.beam_width()
        pgm.energy=float(input.energy())
        pgm.grating.order=int(input.order())
        pgm.cff=float(input.c_ff())
        pgm.grating.line_density=float(input.line_density())
        pgm.mirror.dimensions = [float(input.mirror_length()),float(input.mirror_width()),float(input.mirror_height())]
        pgm.grating.dimensions=[float(input.grating_length()),float(input.grating_width()),float(input.grating_height())]
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
        _ = pgm.propagate(pgm.rays)
        ray2z = [pgm.rays[1].position.list[2],
                pgm.mirror_intercept[1].z,
                pgm.grating_intercept[1].z,
                1000]
        ray3z  = [pgm.rays[2].position.list[2],
                pgm.mirror_intercept[2].z,
                pgm.grating_intercept[2].z,
                1000]
        mirror_footprint_width, mirror_footprint_height = pgm.calc_footprint_size(mirror_intercepts)
        grating_footprint_width, grating_footprint_height = pgm.calc_footprint_size(grating_intercepts)
        ui.update_tooltip("beamfootprint_tooltip", f"Mirror Footprint Size: {mirror_footprint_width:.3f} mm x {mirror_footprint_height:.3f} mm \n Grating Footprint Size: {grating_footprint_width:.3f} mm x {grating_footprint_height:.3f} mm")
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

        fig = go.Figure(layout={'showlegend':True, 
                                'xaxis':{'range':(min(ray3z[1:])-50,max(ray2z[1:-1])+50)}, 
                                'height':500})
        fig.add_trace(go.Scatter(x=mirror_corners[:,0], y=mirror_corners[:,1],fill='toself',fillcolor='red',line={"color":'red'}, marker={'size':0}, name='Mirror', hovertemplate='%{x:.2f} mm, %{y:.2f} mm'))
        fig.add_trace(go.Scatter(x=grating_corners[:,0], y=grating_corners[:,1],fill='toself',fillcolor='blue',line={"color":'blue'}, marker={'size':0}, name='Grating', hovertemplate='%{x:.2f} mm, %{y:.2f} mm'))
        fig.add_trace(go.Scatter(x=mirr_footprint_corners[:,0], y=mirr_footprint_corners[:,1],fill='toself',fillcolor='green',line={"color":'green'}, marker={'size':0}, name='Beam', hovertemplate='%{x:.2f} mm, %{y:.2f} mm'))
        fig.add_trace(go.Scatter(x=grating_footprint_corners[:,0], y=grating_footprint_corners[:,1],fill='toself',fillcolor='green',line={"color":'green'}, marker={'size':0}, showlegend=False,name='Beam', hovertemplate='%{x:.2f} mm, %{y:.2f} mm'))
        fig.update_yaxes(scaleanchor="x",scaleratio=1,)

        fig.update_layout(xaxis_title="Z (mm)", yaxis_title="X (mm)")
        fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=0.18))

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

        if input.calculate_offsets():
            b = float(input.beam_vertical_offset())
            pgm.beam_offset = b
            pgm.mirror.hoffset = float(input.mirror_horizontal_offset())
            pgm.mirror.axis_voffset = -1*b/2
            pgm.mirror.voffset = -1*b
            pgm.mirror.axis_hoffset = 0.
        else:
            pgm.beam_offset = float(input.beam_vertical_offset())
            pgm.mirror.hoffset = float(input.mirror_horizontal_offset())
            pgm.mirror.axis_voffset = float(input.mirror_axis_vertical_offset())
            pgm.mirror.voffset = float(input.mirror_vertical_offset())
            pgm.mirror.axis_hoffset = float(input.mirror_axis_horizontal_offset())
        pgm.beam_width = input.beam_width()
        pgm.energy=float(input.energy())
        pgm.grating.order=int(input.order())
        pgm.cff=float(input.c_ff())
        pgm.grating.line_density=float(input.line_density())
        pgm.mirror.dimensions = [float(input.mirror_length()),float(input.mirror_width()),float(input.mirror_height())]
        pgm.grating.dimensions=[float(input.grating_length()),float(input.grating_width()),float(input.grating_height())]
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
        

        fig = go.Figure(layout={'showlegend':True, 'xaxis':{'range':(min(ray3z[1:])-50,max(ray2z[1:-1])+50),}, 'height':500})
        fig.add_trace(go.Scatter(x=mirror_z, y=mirror_x,fill='toself',fillcolor='red',line={"color":'red'}, marker={'size':0}, name='Mirror', hovertemplate='%{x:.2f} mm, %{y:.2f} mm'))
        fig.add_trace(go.Scatter(x=grating_z, y=grating_x,fill='toself',fillcolor='blue',line={"color":'blue'}, marker={'size':0}, name='Grating', hovertemplate='%{x:.2f} mm, %{y:.2f} mm')) #mode lines if to hide vertices
        fig.update_yaxes(scaleanchor="x",scaleratio=1,)

        fig.add_trace(go.Scatter(x=ray1z, y = ray1x, line={'color':'green', 'width':1.5}, hovertemplate='%{x:.2f} mm, %{y:.2f} mm', name='Centre Ray'))
        fig.add_trace(go.Scatter(x=ray2z, y = ray2x, line={'color':'green', 'width':1.5}, hovertemplate='%{x:.2f} mm, %{y:.2f} mm', name='Upper Ray'))
        fig.add_trace(go.Scatter(x=ray3z, y = ray3x, line={'color':'green', 'width':1.5}, hovertemplate='%{x:.2f} mm, %{y:.2f} mm', name='Lower Ray'))
        fig.update_layout(xaxis_title="Z (mm)", yaxis_title="X (mm)")
        fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0.18))
        return fig
    @render.ui
    @reactive.event(input.angle_tooltip)
    def side_view_angles():
        pgm = PGM(grating=Grating(), mirror=Plane_Mirror())
        pgm.energy=float(input.energy())
        pgm.grating.order=int(input.order())
        pgm.cff=float(input.c_ff())
        pgm.grating.line_density=float(input.line_density())
        alpha, beta = pgm.grating.compute_angles()
        pgm.set_theta()
        theta = pgm.theta
        return ui.TagList(
            ui.tags.div(
                rf"\(\alpha = {alpha:.2f}^\circ\), \(\beta = {beta:.2f}^\circ\), \(\theta = {theta:.2f}^\circ\)"
            ),
            ui.tags.script("MathJax.typesetPromise();"))
    
    
    @reactive.effect
    @reactive.event(input.import_button)
   
    def import_pgm():
        file: list[FileInfo] | None = input.import_pgm()
        if file is None:
            return None
        parser = ConfigParser()
        parser.read( # pyright: ignore[reportUnknownMemberType]
            file[0]["datapath"])
        pgm_keys = [
            'offsets',
            'mirror',
            'grating',
            'core',
            'beam']
        if not all([key in parser.sections() for key in pgm_keys]):
            error_message = ui.modal("The file doesn't meet the specifications.", 
                                     title="Invalid PGM file",
                                     easy_close=True)
            ui.modal_show(error_message)
            return None
        # Loads core parameters
        try:
            ui.update_numeric('energy', value=parser.getfloat('core', 'energy'))
            ui.update_numeric('order', value=parser.getint('core', 'order'))
            ui.update_numeric('c_ff', value=parser.getfloat('core', 'cff'))
            ui.update_numeric('line_density', value=parser.getfloat('grating', 'line_density'))
            # Loads beam parameters
            ui.update_checkbox('calc_beam_height', value=parser.getboolean('beam', 'calculate_from_id'))
            if parser.getboolean('beam', 'calculate_from_id') and 'beam_height' not in parser['beam']:
                ui.update_checkbox('calc_beam_height', value = True)
                ui.update_numeric('electron_size', value=parser.getfloat('beam', 'vert_electron_size'))
                ui.update_numeric('electron_divergence', value=parser.getfloat('beam', 'vert_electron_divergence'))
                ui.update_numeric('distance_to_mirror', value = parser.getfloat('beam', 'distance'))
                ui.update_numeric('length_of_id', value=parser.getfloat('beam', 'id_length'))
                ui.update_numeric('num_of_sigmas', value=parser.getfloat('beam', 'num_of_sigmas'))
            else:
                ui.update_checkbox('calc_beam_height', value=False)
                ui.update_numeric('beam_height', value=parser.getfloat('beam', 'beam_height'))
            ui.update_numeric('beam_width', value=parser.getfloat('beam', 'beam_width'))

            # Loads Mirror Parameters
            ui.update_numeric('mirror_height', value=parser.getfloat('mirror', 'height'))
            ui.update_numeric('mirror_length', value=parser.getfloat('mirror', 'length'))
            ui.update_numeric('mirror_width', value=parser.getfloat('mirror', 'width'))
            # Loads Grating Parameters
            ui.update_numeric('grating_height', value=parser.getfloat('grating', 'height'))
            ui.update_numeric('grating_length', value=parser.getfloat('grating', 'length'))
            ui.update_numeric('grating_width', value=parser.getfloat('grating', 'width'))
            # Loads offsets
            ui.update_checkbox('calculate_offsets', value=parser.getboolean('offsets', 'calculate_offsets'))
            if parser.getboolean('offsets', 'calculate_offsets'):
                ui.update_numeric('beam_vertical_offset', value=parser.getfloat('offsets', 'beam_vertical_offset'))
            else:
                ui.update_checkbox('calculate_offsets', value=False)
                print('in else here')
                ui.update_numeric('beam_vertical_offset', value=parser.getfloat('offsets', 'beam_vertical_offset'))
                ui.update_numeric('mirror_vertical_offset', value=parser.getfloat('offsets', 'mirror_vertical_offset'))
                ui.update_numeric('mirror_axis_horizontal_offset', value=parser.getfloat('offsets', 'mirror_axis_horizontal_offset'))
                ui.update_numeric('mirror_axis_vertical_offset', value=parser.getfloat('offsets', 'mirror_axis_vertical_offset'))
            success_message = ui.modal("The PGM configuration has been successfully imported.",
                                        title="Import Successful",
                                        easy_close=True)
            ui.modal_show(success_message)
        except Exception as e:
            error_message = ui.modal(str(e), title="Error", easy_close=True)
            ui.modal_show(error_message)
            return None
            
    @render.download(filename=input.export_filename)

    def export_pgm():
        parser = ConfigParser()
        parser['core'] = {
            'energy': str(input.energy()),
            'order': str(input.order()),
            'cff': str(input.c_ff())
        }

        if input.calc_beam_height():
            parser['beam'] = {
                'calculate_from_id': str(input.calc_beam_height()),
                'vert_electron_size': str(input.electron_size()),
                'vert_electron_divergence': str(input.electron_divergence()),
                'distance': str(input.distance_to_mirror()),
                'id_length': str(input.length_of_id()),
                'num_of_sigmas': str(input.num_of_sigmas()),
                'beam_width': str(input.beam_width())
            }
        else:
            parser['beam'] = {
                'calculate_from_id': str(input.calc_beam_height()),
                'beam_height': str(input.beam_height()),
                'beam_width': str(input.beam_width())
            }
        parser['mirror'] = {
            'height': str(input.mirror_height()),
            'length': str(input.mirror_length()),
            'width': str(input.mirror_width())
        }
        parser['grating'] = {
            'height': str(input.grating_height()),
            'length': str(input.grating_length()),
            'width': str(input.grating_width()),
            'line_density': str(input.line_density())
        }

        if input.calculate_offsets():
            parser['offsets'] = {
                'calculate_offsets': str(input.calculate_offsets()),
                'beam_vertical_offset': str(input.beam_vertical_offset())
            }
        else:
            parser['offsets'] = {
                'calculate_offsets': str(input.calculate_offsets()),
                'beam_vertical_offset': str(input.beam_vertical_offset()),
                'mirror_vertical_offset': str(input.mirror_vertical_offset()),
                'mirror_horizontal_offset': str(input.mirror_horizontal_offset()),
                'mirror_axis_horizontal_offset': str(input.mirror_axis_horizontal_offset()),
                'mirror_axis_vertical_offset': str(input.mirror_axis_vertical_offset())
            }
        with io.StringIO() as buffer:
            buffer.write("# PGM Configuration File\n\n")
            buffer.write("#pgmweb.diamond.ac.uk\n\n")
            buffer.write('# See pgmweb.diamond.ac.uk/tutorial.html for parameters\n\n')
            buffer.write('# Please consider citing:\n# Wang, Y.P., Walters, A.C., Bazan da Silva, M., et al., PGMweb: An Online Simulation Tool for Plane Grating Monochromators, In preparation.\n\n')

            parser.write(buffer)
            buffer.seek(0)
            
            yield buffer.read()
        



app = App(app_ui, server, static_assets=app_dir)
