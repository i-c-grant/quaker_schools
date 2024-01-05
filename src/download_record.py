import glob
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import click
import img2pdf
import requests
from tqdm import tqdm


@click.command()
@click.argument("jp2_zip_url")
@click.argument("output_path")
def main(jp2_zip_url, output_path):
    output_dir = Path(output_path).parent
    zip_name = "temp_archive.zip"

    output_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(jp2_zip_url, stream=True)
    file_size = int(response.headers.get("Content-Length", 0))

    with tempfile.TemporaryDirectory() as temp_dir_obj:
        temp_dir = Path(temp_dir_obj)

        progress_bar = tqdm(
            desc=jp2_zip_url,
            total=file_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        )

        with open(temp_dir / zip_name, "wb") as f:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                progress_bar.update(size)

        if response.status_code != 200:
            raise Exception("Error downloading zip file.")

        with ZipFile(temp_dir / zip_name, "r") as zip_file:
            zip_file.extractall(temp_dir)

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(*sorted(temp_dir.glob("**/*.jp2"))))

    print(f"PDF file created successfully at {output_path}")


if __name__ == "__main__":
    main()
