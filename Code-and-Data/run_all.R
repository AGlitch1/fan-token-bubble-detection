#!/usr/bin/env Rscript
# Default scope follows the submitted Phase 3 report. Optional paper analyses
# remain available through run_paper_extensions.R.
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
source("R/common.R")
for (p in c("exuber", "cpm", "jsonlite", "digest")) {
  if (!requireNamespace(p, quietly = TRUE)) stop("Missing R package: ", p)
  if (p %in% names(package_versions) && as.character(packageVersion(p)) != package_versions[[p]]) stop("Wrong package version: ", p)
}
source("R/01_process_data.R")
source("R/06_report_alignment.R")
data <- process_data()
run_report_alignment(data)
source("validate_report_alignment.R")
write_report_alignment()
message("Completed report-aligned daily R analysis. See Results/RESULTS.txt")
