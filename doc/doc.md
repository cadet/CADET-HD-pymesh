---
geometry:
    - top=5mm
    - bottom=5mm
    - left=5mm
    - right=5mm
pagestyle: empty
---

# pymesh

```{.mermaid format=pdf}
classDiagram
    class GenericModel{
        +init()
        +set_mesh_size()
        +mesh()
        +write()
    }
    class Column{
        +fragment()
        +separate_volumes()
        +separate_bounding_surfaces()
        +get_inlet_outlet_wires()
        +match_periodic_surfaces()
        +set_individual_physical_groups()
        +set_physical_groups()
        +write()
    }
    class PackedBed{
        -dimTags
        -tags
        +init()
        +read_packing()
        +moveBedToCenter()
        +generate()
    }
    class Container{
    }
    
    GenericModel --|> Column: has
    GenericModel --|> Container: has
    GenericModel --|> PackedBed: has
    Column --> Container: uses
    Column --> PackedBed: uses

```

# Potential New Interfaces

```{.mermaid format=pdf}
classDiagram
    class AbstractModel{
        +init()
        +mesh()
        +write()
    }
    class GenericModel{
        +set_mesh_size()
    }
    class Column{
        +fragment()
        +separate_volumes()
        +separate_bounding_surfaces()
        +get_inlet_outlet_wires()
        +match_periodic_surfaces()
        +set_individual_physical_groups()
        +set_physical_groups()
        +write()
    }
    class PackedBed{
        -beads
        -dimTags
        -tags
        +init()
        +read_packing()
        +moveBedToCenter()
        +generate()
    }
    class Container{
    }
    
    AbstractModel <|-- GenericModel: interfaces
    AbstractModel <|-- MeshCopyModel: interfaces
    
    GenericModel --|> Column: has
    GenericModel --|> Container: has
    GenericModel --|> PackedBed: has
    
    MeshCopyModel --> Column: has

    Column --> Container: uses
    Column --> PackedBed: uses
    
    PackedBed --> Beads: has

```
