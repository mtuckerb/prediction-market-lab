{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
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
}
