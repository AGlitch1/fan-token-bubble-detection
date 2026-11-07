Compile report.tex with pdfLaTeX twice.

  pdflatex -interaction=nonstopmode -halt-on-error report.tex
  pdflatex -interaction=nonstopmode -halt-on-error report.tex

Requires a TeX Live installation with tgtermes, mathptmx, amsmath,
amssymb, graphicx, longtable, array, booktabs, caption, xcolor, microtype,
titlesec, needspace and hyperref. The figures directory must stay beside report.tex.
All prose and tables are editable LaTeX. The original plots are retained as images.
