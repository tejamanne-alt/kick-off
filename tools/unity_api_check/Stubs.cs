// Empty stand-ins for the ugui and Input System packages (not available here), so declarations bind and the compiler
// goes on to check method bodies. Member errors on these types are expected and identical before and after a change.
namespace UnityEngine.EventSystems
{
    public class UIBehaviour : UnityEngine.MonoBehaviour { }
    public class BaseEventData { }
    public class PointerEventData : BaseEventData { }
    public class EventSystem : UIBehaviour { }
    public interface IEventSystemHandler { }
    public interface IPointerDownHandler : IEventSystemHandler { }
    public interface IPointerUpHandler : IEventSystemHandler { }
    public interface IPointerExitHandler : IEventSystemHandler { }
    public interface IPointerEnterHandler : IEventSystemHandler { }
    public interface IPointerClickHandler : IEventSystemHandler { }
    public interface IInitializePotentialDragHandler : IEventSystemHandler { }
    public interface IBeginDragHandler : IEventSystemHandler { }
    public interface IDragHandler : IEventSystemHandler { }
    public interface IEndDragHandler : IEventSystemHandler { }
    public interface IScrollHandler : IEventSystemHandler { }
}
namespace UnityEngine.UI
{
    public class Graphic : UnityEngine.EventSystems.UIBehaviour { protected virtual void OnPopulateMesh(VertexHelper vh) { } }
    public class MaskableGraphic : Graphic { }
    public class Image : MaskableGraphic { }
    public class RawImage : MaskableGraphic { }
    public class Text : MaskableGraphic { }
    public class Selectable : UnityEngine.EventSystems.UIBehaviour { }
    public class Button : Selectable { }
    public class Toggle : Selectable { }
    public class Slider : Selectable { }
    public class InputField : Selectable { }
    public class ScrollRect : UnityEngine.EventSystems.UIBehaviour { }
    public abstract class BaseMeshEffect : UnityEngine.EventSystems.UIBehaviour { public abstract void ModifyMesh(VertexHelper vh); }
    public class VertexHelper { }
    public class CanvasScaler : UnityEngine.EventSystems.UIBehaviour { }
    public class GraphicRaycaster : UnityEngine.EventSystems.UIBehaviour { }
}
namespace UnityEngine.InputSystem
{
    public class InputSystem { }
}
namespace UnityEngine.InputSystem.UI
{
    public class InputSystemUIInputModule : UnityEngine.EventSystems.UIBehaviour { }
}
