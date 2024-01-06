import tempfile
from pathlib import Path
from zipfile import ZipFile

import click
import img2pdf
import requests
from tqdm import tqdm


@click.command()
@click.argument("jp2_zip_url")
@click.argument("output_path")
@click.option("--max-pages", default=50)
def main(jp2_zip_url, output_path, max_pages):
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

        progress_bar.close()

        if response.status_code != 200:
            raise Exception("Error downloading zip file.")

        with ZipFile(temp_dir / zip_name, "r") as zip_file:
            zip_file.extractall(temp_dir)

        file_paths = sorted(temp_dir.glob("**/*.jp2"))
        page_groups = [file_paths[i:i+max_pages] for i in range(0, len(file_paths), max_pages)]

        for i, page_group in enumerate(page_groups):
            output_file_name = f"{str(output_path).rsplit('.', 1)[0]}_{i + 1}.pdf"
            with open(output_file_name, "wb") as f:
                f.write(img2pdf.convert(*page_group))

        print(f"PDF files created successfully.")


if __name__ == "__main__":
    main()
