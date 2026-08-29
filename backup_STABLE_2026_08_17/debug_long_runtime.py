import inspect
import app

print(inspect.getsource(app.run_render))
print("\n--- build_render_kwargs ---")
print(inspect.getsource(app.build_render_kwargs))