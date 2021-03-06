import os

import pypeliner

scripts_directory = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'scripts')


def run_samtools_view(infile, outfile):
    cmd = ['samtools', 'view', '-b', '-F', '1294', infile, '>', outfile]

    pypeliner.commandline.execute(*cmd)


def run_lumpy_extract_split_reads_bwamem(infile, outfile, config):
    cmd = [
        config['samtools'], 'view', '-h', infile, '|',
        config['extractSplitReads_BwaMem'], '-i', 'stdin', '|',
        config['samtools'], 'view', '-Sb', '-',
        '>', outfile
    ]

    pypeliner.commandline.execute(*cmd)


def run_samtools_sort(infile, outfile):
    cmd = ['samtools', 'sort', infile, '-o', outfile]

    pypeliner.commandline.execute(*cmd)


def run_lumpyexpress(lumpy_vcf, config,
                     normal_bam=None,
                     tumour_bam=None,
                     normal_discordants=None,
                     tumour_discordants=None,
                     normal_splitters=None,
                     tumour_splitters=None):
    lumpyexpress = config['lumpyexpress']

    cmd = [lumpyexpress,
           '-B', ','.join([e for e in [normal_bam, tumour_bam] if e]),
           '-S', ','.join([e for e in [normal_splitters, tumour_splitters] if e]),
           '-D', ','.join([e for e in [normal_discordants, tumour_discordants] if e]),
           '-o', lumpy_vcf]

    pypeliner.commandline.execute(*cmd)
