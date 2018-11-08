'''
Created on Feb 21, 2018

@author: pwalters
'''
import pypeliner
import pypeliner.managed as mgd
import tasks
from wgs.utils import vcf_tasks


def create_museq_workflow(
        snv_vcf,
        museqportrait_pdf,
        museqportrait_txt,
        global_config,
        varcall_config,
        sample_id,
        tumour_bam=None,
        normal_bam=None):

    single = False if tumour_bam and normal_bam else True

    workflow = pypeliner.workflow.Workflow()

    workflow.transform(
        name='generate_intervals',
        func=tasks.generate_intervals,
        ctx={'mem': global_config['memory']['low'],
             'pool_id': global_config['pools']['standard'],
             'ncpus': 1, 'walltime': '01:00'},
        ret=mgd.OutputChunks('interval'),
        args=(
            varcall_config['reference'],
            varcall_config['chromosomes']
        )
    )

    if tumour_bam and not normal_bam:
        # Unpaired with only tumour
        workflow.transform(
            name='run_museq_unpaired_tumour',
            ctx={'num_retry': 3, 'mem_retry_increment': 2,
                'mem': global_config['memory']['high'],
                'pool_id': global_config['pools']['multicore'],
                'ncpus': global_config['threads'],
                'walltime': '24:00'},
            axes=('interval',),
            func=tasks.run_museq,
            args=(
                mgd.TempOutputFile('museq.vcf','interval'),
                mgd.TempOutputFile('museq.log', 'interval'),
                varcall_config['reference'],
                mgd.InputInstance('interval'),
                varcall_config['museq_params'],
            ),
            kwargs={
                'tumour_bam': mgd.InputFile(tumour_bam, extensions=['.bai']),
            }
        )
    elif not tumour_bam and normal_bam:
        # Unpaired with only normal
        workflow.transform(
            name='run_museq_unpaired_normal',
            ctx={'num_retry': 3, 'mem_retry_increment': 2,
                'mem': global_config['memory']['high'],
                'pool_id': global_config['pools']['multicore'],
                'ncpus': global_config['threads'],
                'walltime': '24:00'},
            axes=('interval',),
            func=tasks.run_museq,
            args=(
                mgd.TempOutputFile('museq.vcf', 'interval'),
                mgd.TempOutputFile('museq.log', 'interval'),
                varcall_config['reference'],
                mgd.InputInstance('interval'),
                varcall_config['museq_params'],
            ),
            kwargs={
                'normal_bam': mgd.InputFile(normal_bam, extensions=['.bai']),
            }
        )
    else:
        # Paired
        workflow.transform(
            name='run_museq_paired',
            ctx={'num_retry': 3, 'mem_retry_increment': 2,
                'mem': global_config['memory']['high'],
                'pool_id': global_config['pools']['multicore'],
                'ncpus': global_config['threads'],
                'walltime': '24:00'},
            axes=('interval',),
            func=tasks.run_museq,
            args=(
                mgd.TempOutputFile('museq.vcf', 'interval'),
                mgd.TempOutputFile('museq.log', 'interval'),
                varcall_config['reference'],
                mgd.InputInstance('interval'),
                varcall_config['museq_params'],
            ),
            kwargs={
                'tumour_bam': mgd.InputFile(tumour_bam, extensions=['.bai']),
                'normal_bam': mgd.InputFile(normal_bam, extensions=['.bai']),
            }
        )

    workflow.transform(
        name='merge_vcfs',
        ctx={'num_retry': 3, 'mem_retry_increment': 2,
            'mem': global_config['memory']['high'],
            'pool_id': global_config['pools']['multicore'],
            'ncpus': global_config['threads'],
            'walltime': '08:00'},
        func=tasks.merge_vcfs,
        args=(
            mgd.TempInputFile('museq.vcf', 'interval'),
            mgd.TempOutputFile('merged.vcf'),
            mgd.TempSpace('merge_vcf'),
        )
    )


    workflow.transform(
        name='finalise_snvs',
        ctx={'pool_id': global_config['pools']['standard'], 'ncpus': 1, 'walltime': '01:00'},
        func=vcf_tasks.finalise_vcf,
        args=(
            mgd.TempInputFile('merged.vcf'),
            mgd.OutputFile(snv_vcf),
        ),
    )

    workflow.transform(
        name='run_museqportrait',
        ctx={'num_retry': 3, 'mem_retry_increment': 2,
            'mem': global_config['memory']['low'],
            'pool_id': global_config['pools']['standard'],
            'ncpus': 1, 'walltime': '08:00'},
        func=tasks.run_museqportrait,
        args=(
            mgd.InputFile(snv_vcf),
            mgd.OutputFile(museqportrait_pdf),
            mgd.OutputFile(museqportrait_txt),
            mgd.TempOutputFile('museqportrait.log'),
            single,
            varcall_config['plot_params'],
            sample_id
        ),
    )

    return workflow
