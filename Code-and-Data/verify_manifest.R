#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
source("R/common.R")
m <- read_table("../MANIFEST_SHA256.csv")
for (i in seq_len(nrow(m))) {
  p <- file.path("..", m$path[i])
  if (!file.exists(p) || file.info(p)$size != m$bytes[i] || digest::digest(p, algo = "sha256", file = TRUE, serialize = FALSE) != m$sha256[i]) stop("Manifest mismatch: ", m$path[i])
}
message("Verified ", nrow(m), " files against SHA-256 inventory")
