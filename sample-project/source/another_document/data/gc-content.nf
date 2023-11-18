#!/usr/bin/env nextflow

nextflow.enable.dsl=2

params.input_dir = "fasta_files/*.fa"

workflow {

    main:
    fasta_files = Channel.fromPath(params.input_dir)

    gc_content(fasta_files)
    
    // Collect all outputs into a list before sending to collect_gc process
    all_gc_files = gc_content.out.gc_contents.collect()

    collect_gc(all_gc_files)

}

process gc_content {

    publishDir "gc"

    input:
    path fasta_file

    output:
    path "${fasta_file.baseName}.gc_content", emit: gc_contents

    script:
    """
    GC=\$(infoseq -noheading -auto -only -pgc ${fasta_file})
    echo "${fasta_file.baseName}: \$GC" > ${fasta_file.baseName}.gc_content
    """

}

process collect_gc {

    publishDir "result"

    input:
    path gc_content_files

    output:
    path "gc_table.txt"

    script:
    """
    cat ${gc_content_files} > gc_table.txt
    """

}