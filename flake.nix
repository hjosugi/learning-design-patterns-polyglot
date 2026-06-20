{
  description = "Development shell for polyglot design-pattern labs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = [
              pkgs.python3
              pkgs.nodejs
              pkgs.jdk
              pkgs.kotlin
            ];

            shellHook = ''
              echo "learning-design-patterns-polyglot dev shell"
              echo "Try: python3 projects/strategy-discount/python/test_strategy.py"
              echo "Try: node projects/observer-events/javascript/events.test.mjs"
            '';
          };
        });
    };
}
