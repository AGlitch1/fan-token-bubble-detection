options(stringsAsFactors = FALSE, warn = 1)
Sys.setenv(TZ = "UTC", OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1")
local_library <- normalizePath(file.path("..", ".R-library"), mustWork = FALSE)
if (dir.exists(local_library)) .libPaths(c(local_library, .libPaths()))
source("Configuration/analysis_config.R")
paths <- list(raw = "Raw-data", clean = "Processed-data", results = "Results", figures = "Figures")
for (p in paths) dir.create(p, recursive = TRUE, showWarnings = FALSE)

write_table <- function(x, file) {
  write.csv(x, file, row.names = FALSE, na = "", fileEncoding = "UTF-8")
}
read_table <- function(file) read.csv(file, check.names = FALSE, na.strings = c("", "NA", "NaN"))
bind_rows <- function(items, empty) if (length(items)) do.call(rbind, items) else empty
safe_scale <- function(x) {
  if (!is.finite(sd(x)) || sd(x) == 0) stop("Cannot standardize a constant series")
  as.numeric(scale(x))
}
# Never bridge an unobserved calendar period when applying a time-series model.
monthly_blocks <- function(x) {
  x <- x[order(x$date), ]
  key <- as.integer(format(x$date, "%Y")) * 12L + as.integer(format(x$date, "%m"))
  split(x, cumsum(c(TRUE, diff(key) != 1L)))
}
longest_monthly_block <- function(x) {
  blocks <- monthly_blocks(x)
  blocks[[which.max(vapply(blocks, nrow, integer(1)))]]
}
package_versions <- c(exuber = "1.1.0", cpm = "2.3", bsts = "0.9.11",
  forecast = "8.24.0", urca = "1.3.4", vars = "1.6.1", MCS = "0.1.3",
  multDM = "1.1.5", Metrics = "0.1.4")
check_packages <- function() {
  for (p in c(names(package_versions), "jsonlite", "digest")) {
    if (!requireNamespace(p, quietly = TRUE)) stop("Missing R package: ", p, ". Run install_packages.R first.")
    if (p %in% names(package_versions) && as.character(packageVersion(p)) != package_versions[[p]])
      stop("Package ", p, " must be version ", package_versions[[p]], "; run install_packages.R")
  }
}
