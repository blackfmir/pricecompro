from sqlalchemy import Text

extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # як і в supplier_products
