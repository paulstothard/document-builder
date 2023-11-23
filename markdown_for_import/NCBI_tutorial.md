# NCBI

## NCBI Nucleotide

### Search 1

1. Go to [NCBI Nucleotide](https://www.ncbi.nlm.nih.gov/nucleotide/).
2. Search using the query `myostatin AND human[organism]`.
3. In the results page note that there are several links on the left for accessing subsets of results based on, for example, molecule type or source database. Click on **mRNA** under **Molecule types** to access the records for mRNA sequences.
4. Scroll down to the record with the title [Homo sapiens WAP, follistatin/kazal, immunoglobulin, kunitz and netrin domain containing 2 (WFIKKN2), transcript variant 1, mRNA](https://www.ncbi.nlm.nih.gov/nuccore/NM_001330341.2) and click on the title to view the sequence record in GenBank format.
5. Scroll down to the feature table in this record. Note that the gene producing this mRNA sequence is called **WFIKKN2**. This gene is not the myostatin gene. Why was this record returned by the search `myostatin AND human[organism]`? The search qualifiers (the keywords in square brackets) control which parts of the records are searched for matches to the adjacent query text. When a qualifier is omitted all searchable fields are searched. Although this record is not for a myostatin mRNA, in contains the word "myostatin" in several other fields, thus it was returned by the search.
6. Look in the **search details** text box on the right of the search results. It contains the processed query that yielded the displayed results and in this example should contain the text `myostatin[All Fields] AND "Homo sapiens"[Organism] AND biomol_mrna[PROP]`. The `[All Fields]` qualifier is added by the search system when no qualifier is provided for a query word. `"Homo sapiens"[Organism]` is what `human[organism]` is converted to by the search system and `biomol_mrna[PROP]` was added to the query when the **mRNA** link was clicked. The `PROP` refers to "properties" and is a way of restricting the search to certain types of molecules.

## NCBI Nucleotide

### Search 2

1. The myostatin gene in humans is called MSTN. Search NCBI Nucleotide using the query `MSTN[gene name] AND human[organism]`.
2. Note that this search, which uses more precise syntax, returns a smaller number of hits. All the hits correspond to the human MSTN gene.

## A link to a random photo

![A random photo](https://picsum.photos/200/300)
