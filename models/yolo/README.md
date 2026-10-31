# YOLO model weights for CIG

Place your own **best.pt** here on your Windows development machine:

`A:\tania\CIG-new\models\yolo\best.pt`

The `*.pt` Git ignore rule ensures these large model weights are **not** uploaded to GitHub.

**Important:** The uploaded `CIG-new-v2.zip` did not contain `best.pt`, and its Flask `/scan-makanan` route is still a placeholder. Merely copying the model does not activate scanning. Actual integration requires the Ultralytics runtime, class-index mapping for carbohydrate/protein/vegetable/fruit, mask-area calculations, image validation and result UI. A scan must never fabricate nutrition/calorie/gram values from mask area.

Keep the model file private until you verify its provenance and deployment requirements. For production hosting, configure durable model storage or include the weights in an explicit deployment process (not the normal Git repository).
