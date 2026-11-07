#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
source("R/common.R")
rmarkdown::render("Paper-extensions.Rmd", params = list(regenerate = FALSE), quiet = TRUE)
source("R/05_report.R")
write_inventory()
