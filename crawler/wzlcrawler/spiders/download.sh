#!/bin/sh

# Check if curl is installed
if ! command -v curl &>/dev/null; then
  echo "Error: curl is not installed. Please install curl to use this script."
  exit 1
fi

#temp_cache_file="temp_cache.txt"

# Loop through each URL from stdin
while read -r url; do
  # Calculate the filename based on the SHA1 hash of the URL
  filename=$(echo -n "$url" | sha1sum | cut -d' ' -f1).pdf

  # Check if the file already exists
  if [ -e "$filename" ]; then
    echo "File '$filename' already exists. Skipping download for URL: $url"
  else
    # Attempt to download the PDF
    curl -o "$filename.tmp" -fsSL "$url"
    
    # Check if the download was successful
    if [ $? -eq 0 ]; then
      # Rename the temporary file to the desired filename
      mv "$filename.tmp" "$filename"
      echo "Downloaded: $url -> $filename"
    else
      echo "Failed to download: $url"
      rm "$filename.tmp"  # Remove the temporary file in case of a failed download
    fi
  fi

  ## Add the URL to the cache file
  #echo "$url" >> "$temp_cache_file"
done

## Clean up the temporary cache file
#rm "$temp_cache_file"

