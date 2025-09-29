import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class ImageGrid(tk.Frame):
    rows: int
    cols: int
    img_width: int
    img_height: int
    click_callback: callable
    images: list[ImageTk.PhotoImage | None]
    labels: list[tk.Label]
    def __init__(
            self,
            master: tk.Tk,
            rows: int = 4,
            cols: int = 5,
            img_width: int = 300,
            img_height: int = 200,
            click_callback: callable = None,
            **kwargs
    ):
        super().__init__(master, **kwargs)
        self.rows = rows
        self.cols = cols
        self.img_width = img_width
        self.img_height = img_height
        self.click_callback = click_callback
        self.images = []
        self.labels = []
        self._create_grid()

    def _create_grid(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                label = tk.Label(self, image=self._placeholder(), bg='#f0f0f0', relief='ridge', borderwidth=0)
                label.grid(row=r, column=c, padx=5, pady=5)
                label.bind('<Button-1>', lambda e, idx=len(self.labels): self.click_callback(idx) if self.click_callback else None)
                self.labels.append(label)
                self.images.append(None)

    def _placeholder(self) -> ImageTk.PhotoImage:
        img = Image.new('RGB', (self.img_width, self.img_height), color='#dddddd')
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 5, self.img_width - 5, self.img_height - 5], outline='#999999', width=2)
        return ImageTk.PhotoImage(img)

    def _add_img(self, img_path: str, idx: int) -> None:
        img = Image.open(img_path).resize((self.img_width, self.img_height), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.images[idx] = img_tk
        self.labels[idx].config(image=img_tk)

    def _remove_img(self, idx: int) -> None:
        self.images[idx] = None
        self.labels[idx].config(image=self._placeholder())

    def __setitem__(self, idx: int, value: str | None) -> None:
        if idx >= len(self.images) or idx < 0:
            raise IndexError('Index out of range for image grid.')

        if value is None:
            self._remove_img(idx)
        elif isinstance(value, str):
            self._add_img(value, idx)
        else:
            raise ValueError('Value must be a file path or None.')


if __name__ == '__main__':
    def on_image_click(idx: int) -> None:
        print(f"Image {idx} clicked!")

    root = tk.Tk()
    grid = ImageGrid(root, click_callback=on_image_click)
    grid.pack(padx=10, pady=10)

    from image_handler import ImageHandler
    images = ImageHandler()

    grid[0] = images[0]
    grid[1] = images[1024]

    root.mainloop()
