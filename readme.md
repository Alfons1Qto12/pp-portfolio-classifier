# pp-portfolio-classifier

**UPDATE (June 2026)**:
- Morningstar has recently made various changes which affected the script.
- Current situation is that "new-api-branch" does not work anymore.
- However, "main" branch (this branch) has been modified and now functions again.
- Note that "main" branch has less features than "new-api-branch".
- Current solution is less user-friendly. User needs to manually copy an authentication token from a Morningstar Website into into the code of the python script. Script relies on manually maintained mapping between ISIN and SecId of Morningstar. When mapping is unknown, user is prompted for input and input is stored in isin2secid.json (which user might need to edit to modify existing entries).

Python script that automatically classifies funds/ETFs (for stocks) managed in [Portfolio Performance](https://www.portfolio-performance.info/) files by the asset types, sectors, regions, and countries they are invested in. Furthermore it determines the Top 10 holdings of each fund. The classifier uses the information from Morningstar as a data source for classification.

Based on the script by fbuchinger and fizban99.

This version of the script contains a major modification and additional features. Instead of creating taxonomies anew, it updates existing ones (if they exist). This has the advantage that e.g. colours and balancing weights set by the user are maintained. If you want to preserve the earlier versions, please duplicate and rename them before running the script. If you want taxonomies to be created from scratch as in the original version, please delete or rename them before running the script. Note that the script keeps previously obtained classifications of a fund/ETF, if the instrument is inactive or if no information can be retrieved from Morningstar for the corresponding taxonomy. Note also that holdings are kept as classifications in the taxonomy 'Holding' even if they are no longer associated with any security.

Furthermore, there are the following improvements/features: Script now retrieves data for all active funds/ETFs in the file (not just for those having transactions). Script avoids category entries with zero weight. Script tries to round total sum of a taxonomy to 100% (or less) when it slightly exceeds 100%. Script ignores negative weights and rounds individual weight of a category down to 100%, if it exceeds 100%. Script is more verbose and informs user more about its activities. Script dumps the retrieved data into pp_data_fetched.csv (which is overwritten in each run).

Further addition: Script now supports a mechanism to retrieve classification for funds/ETFs from an alternative ISIN. It is used when Morningstar data for the native ISIN does not contain classification for a taxonomy. User needs to add #PPC:[ISIN2=*XY0011223344*] with the desired ISIN value to note field of the security in PP (besides other content). (This does not work for individual stocks.)

Latest addition (Oct 2024): Script now also tries to retrieve classifications for stocks when `-stocks` is added to command line.
 
## Warnings & Known Issues
- Experimental software - use with caution! 
- Check the [Portfolio Performance Forum thread](https://forum.portfolio-performance.info/t/automatic-import-of-classifications/14672)
- If you have issues with fetching data, try deleting the file cache.sqlite. Sometimes this helps :-).

## Installation
requires Python 3, git and Portfolio Performance.
Steps:
1. `git clone` this repository
2. in the install directory run `pip3 install -r requirements.txt`
3. before every run, make sure that you copy a valid authentication token from Morningstar web site into the Python code.
4. test the script by running either `python portfolio-classifier.py test/multifaktortest.xml` or `python portfolio-classifier.py test/multifaktortest.xml -stocks`. (The latter also updates the stocks included in the the xml file). Then open the resulting file `pp_classified.xml` in Portfolio Performance.

## How it works:

**Important: Be aware that the script will overwrite some of your data in the Portfolio Performance file -> risk of data loss. Always make sure that you still have a copy you can fall back to.**

1. In Portfolio Performance, save a copy of your portfolio file as unencrypted XML. The script won't work with any other format (i.e. it also doesn't work with the more recent 'XML with "id" attributes' format of Portfolio Performance).
2. Run the script `python portfolio-classifier.py <input_file> [<output_file>] [-stocks]` If output file is not specified, a file called pp_classified.xml will be created.
3. open pp_classified.xml (or the given output_file name) in Portfolio Performance and check out the modified or added taxonomies and classifications.
4. isin2secid.json contains the mapping of ISINs to Morningstar SecIds (which needs to be provided by the user). Edit (or delete) that file, if the mapping does not match.


## Gallery

### Autoclassified stock-style
<img src="docs/img/autoclassified-stock-style.png" alt="Autoclassified Security types" width="600"/>



### Autoclassified Regions
<img src="docs/img/autoclassified-regions.png" alt="Autoclassified Regions" width="600"/>



### Autoclassified Sectors
<img src="docs/img/autoclassified-sectors.png" alt="Autoclassified Sectors" width="600"/>



### List of stocks and holdings from Top 10 of each fund
<img src="docs/img/top-10-holdings.png" alt="Holdings from Top 10" width="600"/>
