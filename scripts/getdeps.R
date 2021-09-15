lib <- here::here("htmltools/lib")
unlink(lib, recursive = TRUE)

get_package_version <- function(pkg) {
  url <- paste0("https://unpkg.com/", pkg)
  url_long <- httr::GET(url)$url
  url_suffix <- substr(url_long, nchar(url) + 1, nchar(url_long))
  sub("^@", "", strsplit(url_suffix, "/")[[1]][1])
}

pkgs <- c("react", "react-dom")
versions <- lapply(pkgs, get_package_version)
versions <- setNames(versions, pkgs)

download_to_lib <- function(pkg, files) {
  pkg_dir <- file.path(lib, pkg)
  dir.create(pkg_dir, recursive = TRUE)
  owd <- setwd(pkg_dir)
  on.exit(setwd(owd))
  urls <- file.path("https://unpkg.com", paste0(pkg, "@", versions[[pkg]]), files)
  invisible(lapply(urls, function(url) download.file(url, basename(url))))
}

# TODO: include esm and source maps (for umd)
download_to_lib("react", "umd/react.production.min.js")
download_to_lib("react-dom", "umd/react-dom.production.min.js")

cat(
  paste("versions =", jsonlite::toJSON(versions, auto_unbox = TRUE)),
  file = file.path(lib, "../versions.py")
)
