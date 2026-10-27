// Taptic Engine feedback for Dribble To School (called from Audio/Haptics.cs).
#import <UIKit/UIKit.h>

extern "C" {

void DTS_HapticImpact(int style)
{
    UIImpactFeedbackStyle s = style == 0 ? UIImpactFeedbackStyleLight
                            : style == 1 ? UIImpactFeedbackStyleMedium
                                         : UIImpactFeedbackStyleHeavy;
    UIImpactFeedbackGenerator *generator = [[UIImpactFeedbackGenerator alloc] initWithStyle:s];
    [generator prepare];
    [generator impactOccurred];
}

void DTS_HapticSuccess(void)
{
    UINotificationFeedbackGenerator *generator = [[UINotificationFeedbackGenerator alloc] init];
    [generator prepare];
    [generator notificationOccurred:UINotificationFeedbackTypeSuccess];
}

void DTS_HapticSelection(void)
{
    UISelectionFeedbackGenerator *generator = [[UISelectionFeedbackGenerator alloc] init];
    [generator prepare];
    [generator selectionChanged];
}

}
