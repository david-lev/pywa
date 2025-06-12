from pywa.types.flows import *  # noqa

image_carousel = FlowJSON(
    version="7.1",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            terminal=True,
            title="Demo screen",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    ImageCarousel(
                        scale_type=ScaleType.COVER,
                        images=[
                            ImageCarouselItem(
                                alt_text="Landscape image",
                                src="iVBORw0KGgoAAAANSUhEUgAAAB4AAAAKCAIAAAAsFXl4AAAANElEQVR4nGL5ctWagWjwuH0b8YqZiFdKKhg1Gg2wzOawIV61t1AF8YqHZoAMTaMBAQAA",
                            ),
                            ImageCarouselItem(
                                alt_text="Square image",
                                src="iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAALElEQVR4nGIRPRrBgATeWLsjc5kY8AKaSrPIL3FA5i9evZNudhOQBgQAAP",
                            ),
                            ImageCarouselItem(
                                alt_text="Portrait image",
                                src="iVBORw0KGgoAAAANSUhEUgAAAAoAAAAUCAIAAAA7jDsBAAAALUlEQVR4nGIJWfabAQls8DVA5jIx4AUjVZqRP2AJMn",
                            ),
                        ],
                    ),
                    Footer(
                        label="Continue",
                        on_click_action=CompleteAction(),
                    ),
                ],
            ),
        ),
    ],
)
