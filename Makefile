.PHONY: format export-deps package clean

format:
	black .
	isort .

export-deps:
	uv export --format requirements.txt  --no-hashes --no-annotate --no-header -o requirements.txt
	cp requirements.txt adbpg_model/requirements.txt
	cp requirements.txt adbpg_tool/requirements.txt
	cp requirements.txt adbpg_endpoint/requirements.txt

package:
	make clean
	@mkdir -p build
	@dify plugin package ./adbpg_model -o ./build/adbpg_model.difypkg
	@dify plugin package ./adbpg_tool -o ./build/adbpg_tool.difypkg
	@dify plugin package ./adbpg_endpoint -o ./build/adbpg_endpoint.difypkg
	@dify bundle append package . -p ./build/adbpg_model.difypkg
	@dify bundle append package . -p ./build/adbpg_tool.difypkg
	@dify bundle append package . -p ./build/adbpg_endpoint.difypkg
	@dify bundle package . -o ./build/adbpg-bundle-$$(date +%Y%m%d%H%M%S).difybndl
	@dify bundle remove . -i 0
	@dify bundle remove . -i 0
	@dify bundle remove . -i 0


clean:
	find _assets -maxdepth 1 -type f ! -name "*.svg" -delete
	rm -rf build