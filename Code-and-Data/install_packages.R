#!/usr/bin/env Rscript
# Native R alternative to the author's Docker environment. No Python is used.
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
lib <- normalizePath(file.path("..", ".R-library"), mustWork = FALSE)
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
options(repos = c(CRAN = "https://cloud.r-project.org"))
if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes", lib = lib)
source("R/common.R")
versions <- c(package_versions, jsonlite = "2.0.0", digest = "0.6.39", knitr = "1.50", rmarkdown = "2.30")
for (p in names(versions)) {
  current <- if (requireNamespace(p, quietly = TRUE)) as.character(packageVersion(p)) else ""
  if (current != versions[[p]]) remotes::install_version(p, version = versions[[p]], lib = lib, upgrade = "never", dependencies = NA)
}
message("Packages installed in ", lib)
