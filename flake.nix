{
  description = "Prediction Market Lab development shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python311
              pkgs.gnumake
            ];

            shellHook = ''
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
              export PML_DATA_DIR="''${PML_DATA_DIR:-$HOME/.local/share/prediction-market-lab}"
              mkdir -p "$PML_DATA_DIR"
              echo "Prediction Market Lab dev shell"
              echo "  PYTHONPATH=$PYTHONPATH"
              echo "  PML_DATA_DIR=$PML_DATA_DIR"
              echo "Run: make check"
              echo "TUI: python -m prediction_market_lab.tui"
            '';
          };
        });
    };
}
