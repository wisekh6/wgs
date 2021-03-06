import os

import pypeliner
import pypeliner.managed as mgd
from wgs.utils import helpers
from wgs.workflows import remixt
from wgs.workflows import titan


def call_copynumber(
        samples, config, tumours, normals, breakpoints,
        titan_raw_dir, remixt_results,
        remixt_raw_dir, titan_segments, titan_params, titan_markers
):
    breakpoints = dict([(sampid, breakpoints[sampid])
                        for sampid in samples])
    remixt_results = dict([(sampid, remixt_results[sampid])
                           for sampid in samples])
    titan_segments = dict([(sampid, titan_segments[sampid])
                           for sampid in samples])
    titan_params = dict([(sampid, titan_params[sampid])
                         for sampid in samples])
    titan_markers = dict([(sampid, titan_markers[sampid])
                          for sampid in samples])

    workflow = pypeliner.workflow.Workflow()

    workflow.setobj(
        obj=mgd.OutputChunks('sample_id'),
        value=samples)

    workflow.subworkflow(
        name='titan',
        func=titan.create_titan_workflow,
        axes=('sample_id',),
        args=(
            mgd.InputFile('tumour_bam', 'sample_id', fnames=tumours, extensions=['.bai']),
            mgd.InputFile('normal_bam', 'sample_id', fnames=normals, extensions=['.bai']),
            mgd.Template(titan_raw_dir, 'sample_id'),
            mgd.OutputFile('titan_segments', 'sample_id', fnames=titan_segments),
            mgd.OutputFile('titan_params', 'sample_id', fnames=titan_params),
            mgd.OutputFile('titan_markers', 'sample_id', fnames=titan_markers),
            config['globals'],
            config['cna_calling'],
            config['cna_calling']['titan_intervals'],
        ),
    )

    workflow.subworkflow(
        name='remixt',
        func=remixt.create_remixt_workflow,
        axes=('sample_id',),
        args=(
            mgd.InputFile('tumour_bam', 'sample_id', fnames=tumours, extensions=['.bai']),
            mgd.InputFile('normal_bam', 'sample_id', fnames=normals, extensions=['.bai']),
            mgd.InputFile('breakpoints', 'sample_id', fnames=breakpoints),
            mgd.InputInstance('sample_id'),
            config['cna_calling']['remixt_refdata'],
            mgd.OutputFile('remixt_results', 'sample_id', fnames=remixt_results),
            mgd.Template(remixt_raw_dir, 'sample_id'),
            config['cna_calling']['min_num_reads']
        ),
    )

    return workflow


def cna_calling_workflow(args):
    pyp = pypeliner.app.Pypeline(config=args)
    workflow = pypeliner.workflow.Workflow()

    config = helpers.load_yaml(args['config_file'])
    inputs = helpers.load_yaml(args['input_yaml'])

    tumours = helpers.get_values_from_input(inputs, 'tumour')
    normals = helpers.get_values_from_input(inputs, 'normal')
    targets = helpers.get_values_from_input(inputs, 'target_list')
    breakpoints = helpers.get_values_from_input(inputs, 'breakpoints')
    samples = tumours.keys()

    cna_outdir = os.path.join(args['out_dir'], 'copynumber', '{sample_id}')
    remixt_results_filename = os.path.join(cna_outdir, 'remixt', 'results.h5')
    remixt_raw_dir = os.path.join(cna_outdir, 'remixt', 'raw_data')

    titan_raw_dir = os.path.join(cna_outdir, 'titan')
    titan_segments_filename = os.path.join(titan_raw_dir, 'segments.h5')
    titan_markers_filename = os.path.join(titan_raw_dir, 'markers.h5')
    titan_params_filename = os.path.join(titan_raw_dir, 'params.h5')

    workflow.setobj(
        obj=mgd.OutputChunks('sample_id'),
        value=samples)

    workflow.subworkflow(
        name='titan',
        func=titan.create_titan_workflow,
        axes=('sample_id',),
        args=(
            mgd.InputFile("tumour.bam", 'sample_id', fnames=tumours,
                          extensions=['.bai'], axes_origin=[]),
            mgd.InputFile("normal.bam", 'sample_id', fnames=normals,
                          extensions=['.bai'], axes_origin=[]),
            mgd.InputFile("target_list", 'sample_id', fnames=targets,
                          axes_origin=[]),
            mgd.Template(titan_raw_dir, 'sample_id'),
            mgd.OutputFile('titan_segments_filename', 'sample_id',
                           axes_origin=[], template=titan_segments_filename),
            mgd.OutputFile('titan_params_filename', 'sample_id',
                           axes_origin=[], template=titan_params_filename),
            mgd.OutputFile('titan_markers_filename', 'sample_id',
                           axes_origin=[], template=titan_markers_filename),
            config['globals'],
            config['cna_calling'],
            config['cna_calling']['titan_intervals'],
            mgd.InputInstance('sample_id'),
        ),
    )

    workflow.subworkflow(
        name='remixt',
        func=remixt.create_remixt_workflow,
        axes=('sample_id',),
        args=(
            mgd.InputFile('tumour_bam', 'sample_id',
                          fnames=tumours, extensions=['.bai']),
            mgd.InputFile('normal_bam', 'sample_id',
                          fnames=normals, extensions=['.bai']),
            mgd.InputFile('destruct_breakpoints', 'sample_id',
                          axes_origin=[], fnames=breakpoints),
            mgd.InputInstance('sample_id'),
            config['cna_calling']['remixt_refdata'],
            mgd.OutputFile('remixt_results_filename', 'sample_id',
                           axes_origin=[], template=remixt_results_filename),
            mgd.Template(remixt_raw_dir, 'sample_id'),
            config['cna_calling']['min_num_reads']
        ),
    )

    pyp.run(workflow)
