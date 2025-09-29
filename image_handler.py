import os


class ImageHandler:
    """
    Class mapping dataset images to unique indexes.
    """
    images: list[str]
    def __init__(self, img_dir: str = 'YOUR_PATH_T0_IMAGES'):
        self.images = []
        # Traverse the directory and get all images in a deterministic order
        for video in sorted(os.listdir(img_dir)):
            if os.path.isdir(f'{img_dir}/{video}'):
                for img in sorted(os.listdir(f'{img_dir}/{video}')):
                    self.images.append(f'{img_dir}/{video}/{img}')

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, index: int) -> str:
        return self.images[index]

    @staticmethod
    def get_frame_info(file_path: str) -> tuple[str, str]:
        """
        Get the video name and frame name from the file path.

        This method expects the file path to be in the format:
        <some_path>/<video_name>/<frame_number>.jpg
        and is used in the DRES sender, so modify it accordingly if the format changes.
        :param file_path: full path to the image
        :return: (video_name, frame_name)
        """
        video, frame = file_path.split('/')[-2:]
        frame = frame.split('.')[0]
        return video, frame