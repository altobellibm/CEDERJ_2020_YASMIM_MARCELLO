from pathlib import Path

class FileManager:

    @staticmethod
    def write_lines_to_file(self, path, content):
        folder = path.parent
        if not folder.exists():
            Path.mkdir(folder)
        self.logger.info('Salvando arquivo %s', path)
        with open(path, 'w', encoding='utf-8') as f:
            for line in content:
                f.write(line)
                f.write('\n')

    @staticmethod
    def clean_folder_recursive(self, path):
        if path.exists():
            if path.is_dir():
                files = path.glob('**/*')
                for f in files:
                    if f.is_file():
                        f.unlink()