// Taptic Engine feedback for Dribble To School (called from Audio/Haptics.cs).
// Generators are created once and kept prepared, so taps fire with no lag.
#import <UIKit/UIKit.h>

static UIImpactFeedbackGenerator *dtsImpact[5];
static UINotificationFeedbackGenerator *dtsNotify;
static UISelectionFeedbackGenerator *dtsSelect;

static UIImpactFeedbackGenerator *DTS_Generator(int style)
{
    if (style < 0 || style > 4) style = 0;
    if (dtsImpact[style] == nil)
    {
        UIImpactFeedbackStyle s = style == 1 ? UIImpactFeedbackStyleMedium
                                : style == 2 ? UIImpactFeedbackStyleHeavy
                                             : UIImpactFeedbackStyleLight;
        if (@available(iOS 13.0, *))
        {
            if (style == 3) s = UIImpactFeedbackStyleSoft;
            if (style == 4) s = UIImpactFeedbackStyleRigid;
        }
        dtsImpact[style] = [[UIImpactFeedbackGenerator alloc] initWithStyle:s];
    }
    return dtsImpact[style];
}

extern "C" {

// style: 0 light, 1 medium, 2 heavy, 3 soft, 4 rigid. intensity: 0..1.
void DTS_HapticImpactIntensity(int style, float intensity)
{
    UIImpactFeedbackGenerator *generator = DTS_Generator(style);
    if (@available(iOS 13.0, *))
        [generator impactOccurredWithIntensity:intensity];
    else
        [generator impactOccurred];
    [generator prepare];
}

void DTS_HapticImpact(int style)
{
    DTS_HapticImpactIntensity(style, 1.0f);
}

void DTS_HapticSuccess(void)
{
    if (dtsNotify == nil) dtsNotify = [[UINotificationFeedbackGenerator alloc] init];
    [dtsNotify notificationOccurred:UINotificationFeedbackTypeSuccess];
    [dtsNotify prepare];
}

void DTS_HapticSelection(void)
{
    if (dtsSelect == nil) dtsSelect = [[UISelectionFeedbackGenerator alloc] init];
    [dtsSelect selectionChanged];
    [dtsSelect prepare];
}

}
